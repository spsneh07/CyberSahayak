# Implementation Plan

## Phase 0 findings (discovery)

- Repository contained only `gen ai review0.pdf` (review-0 slides: team, problem
  statement, solution bullets, pipeline diagram). No existing code, no git, no
  Docker/env files — so there was nothing to preserve; the structure below is new.
- Tooling available: Python 3.13, Node 25, Docker 29. No local PostgreSQL client,
  so Postgres + pgvector runs in Docker.

## Guiding constraints

- Real pipeline, no hardcoded answers. A `mock` provider exists for tests and
  offline demo, and is clearly labelled in the UI/API (`provider: "mock"`).
- Never invent facts: extraction merges LLM output with deterministic regex
  extraction of identifiers; complaint fields not provided stay as `[PLACEHOLDER]`.
- Tests must run without Docker or API keys (SQLite + mock providers; vector
  search falls back to in-Python cosine similarity when not on PostgreSQL).

## Phases

| # | Scope | Exit criteria |
|---|-------|---------------|
| 0 | Discovery, plan, architecture, ADRs | docs committed |
| 1 | Next.js + FastAPI skeleton, docker-compose (pgvector/pgvector:pg16), `.env.example` | `/health` OK, frontend builds |
| 2 | SQLAlchemy models, Alembic migration, repositories | migration applies; repo tests pass |
| 3 | LLM + embedding provider abstraction, structured output helper, prompts | malformed-output tests pass |
| 4 | Incident extraction + classification | scenario tests pass |
| 5 | KB documents, ingestion (parse→clean→chunk→embed→store), retrieval | RAG tests pass |
| 6 | Explanation, guidance, evidence checklist | tests pass |
| 7 | Complaint + awareness generation | placeholder tests pass |
| 8 | Conversation orchestrator (intent → … → persistence), SSE stage stream | API integration test |
| 9 | UI polish: stages, summary card, sources, complaint editor | `next build` passes |
| 10 | Eval dataset + runner, docs, demo script | all tests green |

## Out of scope (until core works)
Authentication, multi-tenant users, Kubernetes, microservices, file uploads of evidence.
