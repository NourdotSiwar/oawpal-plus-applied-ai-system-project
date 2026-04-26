"""
Tests for the RAG retriever and AI assistant layer.

Retriever tests run without any API key.
AI assistant tests mock the Gemini client so they also run without a key.
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from rag_retriever import retrieve
from ai_assistant import suggest_tasks, answer_question, generate_weekly_schedule
from pawpal_system import Pet


# ── RAG Retriever Tests (no API key needed) ───────────────────────────────────

def test_retriever_returns_results_for_dog_query():
    results = retrieve("daily care feeding walk", {"species": "dog", "breed": "Labrador", "age": 3})
    assert len(results) > 0
    combined = " ".join(r["content"].lower() for r in results)
    assert "dog" in combined or "labrador" in combined


def test_retriever_returns_results_for_cat_query():
    results = retrieve("grooming litter box play", {"species": "cat", "breed": "Persian", "age": 5})
    assert len(results) > 0
    combined = " ".join(r["content"].lower() for r in results)
    assert "cat" in combined or "persian" in combined


def test_retriever_includes_senior_chunk_for_old_pet():
    results = retrieve("care routine health", {"species": "dog", "breed": "Labrador", "age": 9})
    all_tags = [tag for r in results for tag in r.get("tags", [])]
    assert "senior" in all_tags


def test_retriever_includes_puppy_chunk_for_young_pet():
    results = retrieve("feeding schedule", {"species": "dog", "breed": "Lab", "age": 1})
    all_tags = [tag for r in results for tag in r.get("tags", [])]
    assert "puppy" in all_tags or "feeding" in all_tags


def test_retriever_respects_top_k_limit():
    results = retrieve("dog cat pet care grooming dental vet", top_k=2)
    assert len(results) <= 2


def test_retriever_returns_empty_for_unrelated_query():
    results = retrieve("quantum blockchain cryptocurrency nft solidity")
    assert results == []


def test_retriever_no_pet_info_still_works():
    results = retrieve("how often should I brush my dog")
    assert isinstance(results, list)


# ── AI Assistant Tests (Gemini mocked) ───────────────────────────────────────

def _make_pet(name="Buddy", species="dog", breed="Labrador", age=3, medical_info="None"):
    return Pet(pet_id=1, name=name, species=species, breed=breed, age=age, medical_info=medical_info)


def _mock_groq_response(json_payload: dict):
    """Return a mock that makes _call() return json_payload as text via Groq chat completions."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(json_payload)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_suggest_tasks_returns_tasks_and_confidence():
    payload = {
        "tasks": [
            {"description": "Morning walk", "time": "08:00", "frequency": "Daily"},
            {"description": "Feeding", "time": "07:30", "frequency": "Daily"},
        ],
        "confidence": 0.9,
        "reasoning": "Labradors need exercise and regular feeding.",
    }
    with patch("ai_assistant._get_client", return_value=_mock_groq_response(payload)):
        result = suggest_tasks(_make_pet())

    assert len(result["tasks"]) == 2
    assert result["confidence"] == 0.9
    assert "reasoning" in result


def test_suggest_tasks_gracefully_handles_api_error():
    with patch("ai_assistant._get_client", side_effect=RuntimeError("API error")):
        result = suggest_tasks(_make_pet())

    assert result["tasks"] == []
    assert result["confidence"] == 0.0
    assert "reasoning" in result


def test_answer_question_returns_answer_and_confidence():
    payload = {
        "answer": "Brush a Golden Retriever daily to manage shedding.",
        "confidence": 0.85,
        "sources_used": ["golden retriever grooming guide"],
    }
    with patch("ai_assistant._get_client", return_value=_mock_groq_response(payload)):
        result = answer_question("How often should I brush a Golden Retriever?")

    assert "answer" in result
    assert result["confidence"] == 0.85
    assert isinstance(result["sources_used"], list)


def test_answer_question_gracefully_handles_api_error():
    with patch("ai_assistant._get_client", side_effect=RuntimeError("Network error")):
        result = answer_question("What should I feed my cat?")

    assert result["confidence"] == 0.0
    assert "answer" in result


def test_generate_weekly_schedule_returns_seven_days():
    days = [f"Day {i}" for i in range(7)]
    payload = {
        "schedule": [
            {"day": d, "tasks": [{"pet_name": "Buddy", "description": "Walk", "time": "08:00", "frequency": "Daily"}]}
            for d in days
        ],
        "confidence": 0.88,
        "reasoning": "Schedule balanced across the week.",
    }
    with patch("ai_assistant._get_client", return_value=_mock_groq_response(payload)):
        result = generate_weekly_schedule([_make_pet()])

    assert len(result["schedule"]) == 7
    assert result["confidence"] == 0.88


def test_generate_weekly_schedule_gracefully_handles_api_error():
    with patch("ai_assistant._get_client", side_effect=RuntimeError("Timeout")):
        result = generate_weekly_schedule([_make_pet()])

    assert result["schedule"] == []
    assert result["confidence"] == 0.0
