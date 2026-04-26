# Model Card — PawPal+ AI Assistant

## Model Details

| Field | Value |
|---|---|
| **Model** | `inclusionai/ling-2.6-flash` |
| **Provider** | OpenRouter (free tier, no credit card required) |
| **API** | OpenRouter Chat Completions (`/api/v1/chat/completions`) |
| **Output format** | Structured JSON (tasks, confidence score, reasoning) |
| **Retrieval layer** | Custom keyword-overlap RAG over a 32-chunk pet care knowledge base |

---

## Intended Use

PawPal+ AI Assistant is designed to help everyday pet owners — not veterinary professionals — manage routine pet care. It is scoped to:

- Suggesting daily care tasks tailored to a specific pet's species, breed, and age
- Answering general pet care questions grounded in the knowledge base
- Generating 7-day care schedules for one or more pets

It is **not** intended for medical diagnosis, emergency triage, or advice specific to a pet's individual health history.

---

## Knowledge Base

- 32 curated chunks covering species, common breeds, age groups, feeding, exercise, grooming, vet care, enrichment, and weekly scheduling
- Retrieval uses keyword overlap scoring expanded with species/breed/age-group tags — no external embedding API needed
- The knowledge base can be extended by adding JSON chunks to `knowledge_base.json`

---

## Design Decisions

**RAG over fine-tuning:** A curated knowledge base with keyword retrieval was chosen over fine-tuning because it is transparent, updatable, and requires no training infrastructure.

**Keyword scoring over embeddings:** Embedding-based retrieval would require an external vector API or local model. Keyword overlap scoring achieves good-enough retrieval for structured pet care topics without added complexity or cost.

**JSON-structured AI responses:** Asking the model to return strict JSON (tasks, confidence, reasoning) makes parsing reliable and allows the app to surface confidence scores and reasoning directly in the UI.

**Confidence scores surfaced in UI:** Every AI response shows a confidence percentage so users know how certain the model is. Low-confidence responses prompt the user to verify with a vet.

**Logging for observability:** All AI calls log to `pawpal_ai.log` with timestamp, function, pet profile, number of chunks retrieved, and confidence. This enables post-hoc review of AI performance without instrumenting the UI.

**Graceful degradation:** Every AI function catches exceptions and returns a safe fallback dict with `confidence: 0.0` and an error message so the app never crashes on an API failure.

---

## Testing Results

**Total tests: 17 (7 original + 10 new AI-layer tests)**

Original suite (7 tests): All passing. Covers task completion, pet task assignment, chronological sorting, daily recurrence auto-creation, conflict detection, empty scheduler edge case, and non-conflict for same time on different dates.

New AI-layer suite (10 tests):
- 7 RAG retriever tests — no API key needed; verify that dog/cat/senior/puppy queries return relevant chunks, top-k limit is respected, and unrelated queries return empty.
- 3 AI assistant tests per function — OpenRouter is mocked; verify correct parsing of JSON responses and graceful handling of API errors for `suggest_tasks`, `answer_question`, and `generate_weekly_schedule`.

**What worked well:** Keyword retrieval was surprisingly effective for structured pet care topics. Mocking OpenRouter made the test suite fast and fully offline. Confidence scoring helped identify when the model was uncertain (e.g., exotic pet species not in the knowledge base).

**What didn't work as expected:** The model occasionally returned JSON wrapped in markdown code fences even when the prompt said not to — the `_parse_json` helper strips these. Very rare breeds returned lower-confidence suggestions because fewer knowledge base chunks matched.

**What was learned:** RAG grounding noticeably reduces hallucinations compared to prompting without context. Logging confidence scores across test runs revealed that multi-pet weekly schedules consistently scored lower (~0.83) than single-pet task suggestions (~0.90), likely because the prompt is longer and more ambiguous.

---

## Limitations and Biases

The knowledge base covers common dog and cat breeds but has limited coverage of exotic pets (reptiles, fish, ferrets). Care advice is based on general veterinary guidelines, not the specific medical history of any individual pet. The AI may confidently give advice that a vet would adjust for a pet's unique conditions.

---

## Ethical Considerations

**Could the AI be misused?** A user could follow AI-generated care advice in place of a vet consultation for a sick animal. This is mitigated by:
1. Surfacing confidence scores so low-confidence answers are clearly flagged
2. The knowledge base containing conservative, vet-aligned guidelines
3. All Q&A answers recommending a vet for medical questions

---

## Reflection: AI Collaboration

**What surprised me about testing AI reliability:** Confidence scores from the model were not always correlated with actual answer quality. In some cases, a 0.75 confidence answer was more accurate than a 0.92 one. This reinforced that confidence scores are useful signals but should not be treated as ground truth — human review remains important.

**Helpful AI suggestion:** When designing the RAG retriever, the AI suggested adding age-group keyword expansion (automatically adding "senior" or "puppy" tags to the query based on the pet's age field) rather than requiring the user to phrase the query correctly. This significantly improved retrieval relevance for young and older pets without any extra UI complexity.

**Flawed AI suggestion:** The AI initially suggested using cosine similarity with sentence embeddings for retrieval, citing it as "more accurate." While true in theory, this would have required either a local embedding model (heavy dependency) or a second API (extra cost and latency). The keyword overlap approach was simpler, faster, and sufficient for the structured domain of pet care topics — the AI's suggestion optimised for accuracy in isolation without considering the project's constraints.
