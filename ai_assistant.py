import os
import json
import re
import logging
import requests
from datetime import date, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from rag_retriever import retrieve

load_dotenv()

logging.basicConfig(
    filename="pawpal_ai.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

_MODEL = "inclusionai/ling-2.6-flash:free"
_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _call(prompt: str) -> str:
    """Call OpenRouter API (free tier, no credit card required)."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file and restart the app."
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pawpal-plus.streamlit.app",
        "X-Title": "PawPal+ AI Assistant",
    }
    body = {"model": _MODEL, "messages": [{"role": "user", "content": prompt}]}
    resp = requests.post(_API_URL, headers=headers, json=body, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"{resp.status_code}: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"]


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def suggest_tasks(pet) -> dict:
    """
    Use RAG + Gemini to suggest 5 daily care tasks tailored to a specific pet.

    Retrieves relevant care facts from the knowledge base first, then passes
    that context along with the pet's profile to the LLM.

    Returns:
        dict with keys: tasks (list), confidence (float), reasoning (str)
    """
    pet_info = {"species": pet.species, "breed": pet.breed, "age": pet.age}
    chunks = retrieve(f"{pet.species} {pet.breed} daily care tasks routine", pet_info, top_k=4)
    context = "\n\n".join(c["content"] for c in chunks)

    prompt = f"""You are a professional pet care expert. Suggest exactly 5 specific daily care tasks for this pet.
Use the knowledge base context below to tailor your suggestions.

KNOWLEDGE BASE CONTEXT:
{context or "No specific context found. Use general pet care best practices."}

PET PROFILE:
- Name: {pet.name}
- Species: {pet.species}
- Breed: {pet.breed or "Unknown"}
- Age: {pet.age} years
- Medical notes: {pet.medical_info or "None"}

Return ONLY a valid JSON object with this exact structure and nothing else:
{{
  "tasks": [
    {{"description": "Task description", "time": "HH:MM", "frequency": "Daily"}}
  ],
  "confidence": 0.85,
  "reasoning": "1-2 sentences explaining why these tasks were chosen for this specific pet."
}}"""

    try:
        result = _parse_json(_call(prompt))
        logger.info(
            f"suggest_tasks | pet={pet.name} species={pet.species} age={pet.age} "
            f"| chunks_retrieved={len(chunks)} | confidence={result.get('confidence', 'N/A')}"
        )
        return result
    except Exception as e:
        logger.error(f"suggest_tasks | pet={pet.name} | error={e}")
        return {
            "tasks": [],
            "confidence": 0.0,
            "reasoning": f"Could not generate suggestions: {e}",
        }


def answer_question(question: str, pet=None) -> dict:
    """
    Use RAG + Gemini to answer a pet care question.

    Retrieves relevant knowledge base chunks for the question, then uses the LLM
    to synthesize a helpful answer grounded in that context.

    Returns:
        dict with keys: answer (str), confidence (float), sources_used (list)
    """
    pet_info = {}
    if pet:
        pet_info = {
            "species": getattr(pet, "species", ""),
            "breed": getattr(pet, "breed", ""),
            "age": getattr(pet, "age", 0),
        }

    chunks = retrieve(question, pet_info or None, top_k=4)
    context = "\n\n".join(c["content"] for c in chunks)
    pet_context = (
        f"\nPet context: {pet.name} is a {pet.age}-year-old {pet.breed} {pet.species}."
        if pet
        else ""
    )

    prompt = f"""You are a knowledgeable and friendly pet care assistant.
Answer the question using the knowledge base context provided.
{pet_context}

KNOWLEDGE BASE CONTEXT:
{context or "No specific context found. Answer from general pet care knowledge."}

QUESTION: {question}

Return ONLY a valid JSON object with this exact structure and nothing else:
{{
  "answer": "Your clear, practical, helpful answer here.",
  "confidence": 0.85,
  "sources_used": ["brief description of the knowledge applied"]
}}"""

    try:
        result = _parse_json(_call(prompt))
        logger.info(
            f"answer_question | q='{question[:60]}' | pet={getattr(pet, 'name', 'none')} "
            f"| chunks_retrieved={len(chunks)} | confidence={result.get('confidence', 'N/A')}"
        )
        return result
    except Exception as e:
        logger.error(f"answer_question | q='{question[:60]}' | error={e}")
        return {
            "answer": f"Sorry, I could not generate an answer. Please try again. ({e})",
            "confidence": 0.0,
            "sources_used": [],
        }


def generate_weekly_schedule(pets: list) -> dict:
    """
    Use RAG + Gemini to generate a 7-day care schedule for one or more pets.

    Retrieves care facts for each pet, deduplicates context, and asks the LLM to
    produce a structured weekly plan with an explanation of its reasoning.

    Returns:
        dict with keys: schedule (list of day objects), confidence (float), reasoning (str)
    """
    all_context_parts = []
    for pet in pets:
        pet_info = {"species": pet.species, "breed": pet.breed, "age": pet.age}
        chunks = retrieve(
            f"{pet.species} {pet.breed} weekly care schedule routine", pet_info, top_k=3
        )
        all_context_parts.extend(c["content"] for c in chunks)

    seen = set()
    unique_parts = []
    for part in all_context_parts:
        if part not in seen:
            seen.add(part)
            unique_parts.append(part)
    context = "\n\n".join(unique_parts)

    pets_summary = "\n".join(
        f"- {p.name}: {p.species}, {p.breed or 'unknown breed'}, {p.age} years old"
        for p in pets
    )
    today = date.today()
    week_days = [(today + timedelta(days=i)).strftime("%A %Y-%m-%d") for i in range(7)]

    prompt = f"""You are a professional pet care scheduling expert.
Create a practical 7-day care schedule for the following pets.

KNOWLEDGE BASE CONTEXT:
{context or "Use general pet care best practices."}

PETS:
{pets_summary}

WEEK: {week_days[0]} through {week_days[6]}

Include appropriate tasks for each pet each day: feeding, exercise/play, grooming (as needed),
medication reminders (if applicable), and enrichment activities.

Return ONLY a valid JSON object with this exact structure and nothing else:
{{
  "schedule": [
    {{
      "day": "{week_days[0]}",
      "tasks": [
        {{"pet_name": "PetName", "description": "Task description", "time": "HH:MM", "frequency": "Daily"}}
      ]
    }}
  ],
  "confidence": 0.85,
  "reasoning": "2-3 sentences explaining the schedule design and why it suits these specific pets."
}}"""

    try:
        result = _parse_json(_call(prompt))
        logger.info(
            f"generate_weekly_schedule | pets={[p.name for p in pets]} "
            f"| confidence={result.get('confidence', 'N/A')}"
        )
        return result
    except Exception as e:
        logger.error(f"generate_weekly_schedule | error={e}")
        return {
            "schedule": [],
            "confidence": 0.0,
            "reasoning": f"Could not generate schedule: {e}",
        }
