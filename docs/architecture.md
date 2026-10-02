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
| `services/ai` | `LLMProvider`, `EmbeddingProvider`, providers (mock, OpenAI-compatible, Anthropic), structured-output helper, `prompts/` |
| `services/incident` | extraction, identifier regexes, missing-info detection |
| `services/classification` | taxonomy + classifier |
| `services/rag` | chunking, ingestion, sanitisation, retrieval |
| `services/guidance` | explanation, actions, evidence checklist |
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
