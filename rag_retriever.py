import json
import os
import re
from typing import List, Dict, Optional

KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.json")


def _load_chunks() -> List[Dict]:
    with open(KB_PATH, encoding="utf-8") as f:
        return json.load(f)["chunks"]


def retrieve(query: str, pet_info: Optional[Dict] = None, top_k: int = 4) -> List[Dict]:
    """
    Retrieve the most relevant knowledge base chunks for a query.

    Uses keyword overlap scoring between the query + pet context and each chunk's
    tags and content words. No external embedding API needed.

    Args:
        query: Natural language query or topic string.
        pet_info: Optional dict with keys 'species', 'breed', 'age' to boost relevance.
        top_k: Maximum number of chunks to return.

    Returns:
        List of matching chunk dicts, sorted by relevance score descending.
    """
    chunks = _load_chunks()

    # Build query term set from the query text
    terms = set(re.findall(r"\w+", query.lower()))

    # Expand terms using pet info
    if pet_info:
        for key in ("species", "breed"):
            val = str(pet_info.get(key, "") or "")
            terms.update(re.findall(r"\w+", val.lower()))

        age = pet_info.get("age", 0)
        if isinstance(age, (int, float)):
            if age < 2:
                terms.update({"puppy", "kitten", "young", "junior", "baby"})
            if age >= 8:
                terms.update({"senior", "elderly", "old", "geriatric", "aging"})

    # Score each chunk by word overlap
    scored = []
    for chunk in chunks:
        chunk_terms = set(chunk.get("tags", []))
        chunk_terms.update(re.findall(r"\w+", chunk["content"].lower()))
        score = len(terms & chunk_terms)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]
