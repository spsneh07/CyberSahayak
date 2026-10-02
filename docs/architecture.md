# Architecture

```
Browser (Next.js / React / Tailwind)
   │  REST + Server-Sent Events (stage progress)
   ▼
FastAPI  /api/v1   ──►  ConversationOrchestrator
                          │
     ┌────────────────────┼──────────────────────────────────────┐
     ▼                    ▼                                      ▼
 IntentDetector   IncidentExtractor ─► Validator     Classifier (taxonomy)
                    (LLM + regex)                          │
                                                           ▼
                                         Retriever (embeddings + pgvector)
                                                           │
                    ┌──────────────┬───────────────┬───────┴─────────┐
                    ▼              ▼               ▼                 ▼
               Explanation     Guidance +     ComplaintGenerator  AwarenessGenerator
                               Evidence list  (template + LLM      (LLM, grounded)
                                               narrative)
                                                           │
                                                           ▼
                                         Repositories (SQLAlchemy) ─► PostgreSQL + pgvector
```

## Backend layout (`backend/app`)

| Package | Responsibility |
|---|---|
| `api/v1` | HTTP routes only: validation, status codes, wiring |
| `core` | settings (env), DB session, logging with redaction, error handlers |
| `models` | SQLAlchemy ORM tables |
| `schemas` | Pydantic request/response + LLM structured-output schemas |
| `repositories` | All DB access |
| `services/ai` | `LLMProvider`, `EmbeddingProvider`, providers (mock, OpenAI-compatible incl. Groq, Anthropic; embeddings: hash, local sentence-transformers, OpenAI-compatible), retry/backoff on 429/5xx, structured-output helper, `prompts/` |
| `services/incident` | extraction, identifier regexes, missing-info detection |
| `services/classification` | taxonomy + classifier |
| `services/rag` | chunking, ingestion, sanitisation, retrieval |
| `services/guidance` | explanation, actions, evidence checklist; `safety.py` output guards (no evidence-destruction advice) |
| `services/complaint` | complaint draft |
| `services/awareness` | awareness content |
| `services/conversation` | intent detection + orchestrator |

## Request flow (chat message)

1. Persist user message.
2. Intent: `report_incident | check_message | question | generate_complaint | evidence | tips | smalltalk`.
3. Extraction → merge with previous incident state of the conversation (new facts
   only, never overwrite user facts with inferences) → validate with Pydantic.
4. Classification against fixed taxonomy (confidence, reasoning, alternatives;
   `unknown` allowed).
5. Retrieval: query = category + description; top-k chunks with metadata.
   Chunks are wrapped as quoted data in prompts and scanned for injection patterns.
6. Generation: explanation + guidance + evidence checklist; complaint/awareness on demand.
7. Follow-up questions derived from `missing_information` minus what is known.
8. Persist incident, classification, assistant message; stream stage events.

## Data model

`users, conversations, messages, incidents, classifications, evidence_items,
complaint_drafts, awareness_content, knowledge_documents, knowledge_chunks (vector), feedback`.

## Deployment topology

```
Browser ──► Next.js (3000) ──► FastAPI (8000) ──► PostgreSQL 16 + pgvector (Docker, host port POSTGRES_PORT)
                                   │
                                   ├──► LLM API (OpenAI-compatible e.g. Groq, or Anthropic)   [real mode]
                                   └──► sentence-transformers on CPU (local embeddings)       [real mode]
```

PostgreSQL with pgvector is the application database. SQLite is used only by the automated tests.

## Output guards (deterministic, after every generation)

| Guard | Where |
|---|---|
| Identifiers not literally present in the user's text are dropped; regex-found ones are added | `incident/extractor.py` |
| URLs and helpline-style numbers absent from retrieved sources → `[official … — verify]` | `guidance/advisor.py` |
| Advice to delete/erase/wipe evidence is removed (negated forms kept) | `guidance/safety.py` |
| Citation ids filtered to retrieved ids; awareness links filtered to retrieved URLs; only http(s) links rendered | `guidance`, `awareness`, frontend |
| Complaint narrative identifiers not provided by the user → placeholders | `complaint/generator.py` |
| Query embedding model must match the model used to build the index | `rag/retriever.py` |

## Tests

`tests/unit` (no I/O), `tests/integration` (SQLite + Alembic + API), `tests/postgres` (real pgvector,
opt-in via `TEST_DATABASE_URL`), `tests/real_provider` (real LLM/embeddings, opt-in via
`RUN_REAL_PROVIDER_TESTS=1`).
