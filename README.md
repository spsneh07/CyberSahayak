# AI Cyber Crime Complaint & Awareness Assistant (CyberSahayak)

B.Tech 5th-semester course project — 21CSE306P Applied Generative AI (2026-27).
Team: Ashutosh Bawri, Nikshit R, Riya Maheshwari, Sneh Prasad.

> This assistant provides educational cybersecurity guidance and complaint-drafting assistance. It is not a
> substitute for law enforcement, legal advice, or professional cybersecurity investigation.

## Problem
Cybercrime victims often can't tell what kind of scam happened, what to do first, which evidence to keep or
how to write a formal complaint. Guidance is scattered and written for experts.

## Solution
A conversational assistant that runs every message through a real GenAI pipeline:

```
message → intent → extraction (LLM + regex grounding) → validation (Pydantic)
        → classification (21-class taxonomy) → retrieval (pgvector RAG)
        → explanation + guidance + evidence checklist → complaint draft / awareness
        → persistence (PostgreSQL)
```

The UI shows each stage live (Server-Sent Events), a structured incident summary that marks every fact as
*you said / inferred / unknown*, cited trusted sources, an interactive evidence checklist, an editable
complaint draft with `[PLACEHOLDERS]` for missing facts, and personalised awareness content.

## Architecture & tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript (strict), Tailwind CSS |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 + pgvector (HNSW cosine index) |
| AI | Provider abstraction: OpenAI-compatible (OpenAI/Groq/OpenRouter/Ollama), Anthropic, offline mock; embeddings: OpenAI-compatible or local hash |

Details: [docs/architecture.md](docs/architecture.md), [docs/architecture_decisions.md](docs/architecture_decisions.md), [docs/rag.md](docs/rag.md).

```
backend/app/
  api/v1/          conversations (+SSE stream), incidents, rag, feedback
  core/            config, db, redacting logger, error handlers
  models/          SQLAlchemy tables      repositories/  DB access
  schemas/         Pydantic API + LLM output schemas
  services/ai/     providers, structured output helper, prompts/
  services/{incident,classification,rag,guidance,complaint,awareness,conversation}
backend/alembic/   migrations             backend/tests/   pytest suite
backend/evaluation/ fictional dataset + eval runner
frontend/          Next.js app            knowledge_base/  RAG documents
```

## Setup

Prerequisites: Python 3.12+, Node 20+, Docker (for PostgreSQL + pgvector).

```bash
cp .env.example .env          # then edit: set POSTGRES_PASSWORD, and LLM_* if you have a key
docker compose up -d db
```

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
alembic upgrade head
python -m scripts.ingest_kb
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

Everything in Docker instead: `docker compose up --build`, then run ingestion once:
`docker compose exec backend python -m scripts.ingest_kb`.

No Docker? The backend also runs on SQLite for local development
(`DATABASE_URL=sqlite:///./dev.db`); vector search then falls back to exact in-Python cosine similarity.
Use PostgreSQL + pgvector for the real deployment.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | sqlite dev DB | `postgresql+psycopg://user:pass@host:5432/db` |
| `LLM_PROVIDER` | `mock` | `mock` \| `openai` (any OpenAI-compatible) \| `anthropic` |
| `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY` | | model, endpoint, key |
| `LLM_TEMPERATURE`, `LLM_TIMEOUT_SECONDS` | 0.2, 60 | |
| `EMBEDDING_PROVIDER` | `hash` | `hash` (offline, lexical) \| `openai` |
| `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY` | | |
| `EMBEDDING_DIM` | 384 | must match the migration's vector column |
| `RAG_TOP_K`, `RAG_MIN_SCORE` | 5, 0.05 | retrieval |
| `CORS_ORIGINS` | `http://localhost:3000` | |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | frontend → backend |

Never commit `.env`. Logs redact keys, tokens, emails, UPI IDs, phone and long account numbers.

**Mock mode:** with `LLM_PROVIDER=mock` the app works offline using transparent keyword/regex heuristics in
`services/ai/providers/mock.py`. It exists for tests and offline demos, is labelled "offline mock AI" in the
UI, and is not a language model. Use a real provider for meaningful results.

## Testing

```bash
cd backend && pytest            # 43 tests; no API key or Docker needed
cd frontend && npm run typecheck && npm run build
```

Tests cover phishing, UPI fraud, banking fraud, social-media impersonation, job scam, ambiguous/unknown
incidents, missing information and follow-ups, hallucinated-identifier removal, malformed/invalid LLM
output (repair + fallback), RAG ingestion/retrieval/idempotency/prompt-injection stripping, complaint
placeholders, awareness link filtering, log redaction, API validation errors and the SSE stream. Tests run
the real Alembic migration on a temporary SQLite DB.

**Evaluation:** `python -m evaluation.run_eval` runs the 20-case fictional dataset against the configured
provider and writes `evaluation/results.json`. No accuracy figures are claimed in this repository — run it
with your provider and report what you measure.

## RAG ingestion

Add `.md`/`.txt` files with front-matter (or `.pdf` + `.meta.json`) to `knowledge_base/documents/` and run
`python -m scripts.ingest_kb`. See [knowledge_base/README.md](knowledge_base/README.md) — the seed
documents are team-written summaries linked to official sources; verify before relying on them.

## API

| Method | Path |
|---|---|
| POST | `/api/v1/conversations` |
| GET | `/api/v1/conversations/{id}` |
| POST | `/api/v1/conversations/{id}/messages` (JSON) · `/messages/stream` (SSE) |
| POST | `/api/v1/incidents/analyze` |
| GET | `/api/v1/incidents/{id}` |
| POST | `/api/v1/incidents/{id}/guidance` · `/complaint` · `/awareness` |
| POST | `/api/v1/rag/search` |
| POST | `/api/v1/feedback` |
| GET | `/api/v1/meta`, `/health` |

Interactive docs at http://localhost:8000/docs. Errors share one shape: `{"error": {"code", "message", "details"}}`.

## Limitations
- Seed knowledge base is small and consists of curated summaries, not official full texts.
- Default `hash` embeddings are lexical, not semantic; use an embedding API for better retrieval.
- Mock mode is heuristic; quality depends on the configured LLM.
- No authentication; conversations are anonymous by ID. Do not deploy publicly as-is.
- Complainant details entered for a draft are stored in the draft text.
- English only; India-focused guidance.
- It does not file complaints; users must submit through official channels.

## Future scope
Authentication and user history; multilingual support (Hindi and regional languages); voice input; OCR of
screenshot evidence; ingestion of full official advisories with scheduled refresh; hybrid (BM25 + vector)
retrieval and re-ranking; LLM-as-judge evaluation with a larger, human-labelled dataset; PDF export of the
complaint.
