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

## Status (2026-10-02, production-integration validation)

| Area | Status | Evidence |
|---|---|---|
| PostgreSQL | Verified | `pgvector/pgvector:pg16` container (PostgreSQL 16.15), host port 5433; Alembic `0001`+`0002` applied |
| pgvector | Verified | extension 0.8.7; `knowledge_chunks.embedding vector(384)`; HNSW `vector_cosine_ops` index; `<=>` search; `tests/postgres` 5/5 |
| Semantic embeddings | Verified | local `all-MiniLM-L6-v2`; 10 docs → 21 chunks re-embedded; all norms 1.0; paraphrase test passes |
| Real LLM | Verified | Groq `openai/gpt-oss-120b` (script demo + evaluation) and `openai/gpt-oss-20b` (real-provider tests + web UI demo) |
| RAG | Verified with known misses | 5 manual queries + hit@3 15/18 on the eval set (see `docs/rag.md`) |
| End-to-end demo | Verified in the web UI | extraction, classification, retrieval, explanation, guidance, evidence, complaint, awareness, follow-up |
| Evaluation | Measured | `docs/project_explanation.md#evaluation` |
| Docker | Verified build | backend (with `INSTALL_ML=true`, 3.62 GB) and frontend (303 MB) images build; backend image imports app + sentence-transformers |

Bugs found and fixed during validation: duplicate retrieval of the same document; stale vectors after
switching embedding model (now re-embedded and mismatched queries refused); stage events emitted twice;
evidence-deletion advice from the real LLM (deterministic filter); complaint narrative replacing a stated
date with a placeholder (prompt); provider errors not diagnosable (status + message now logged); no
429 handling (bounded backoff); non-http source URLs renderable as links; financial-loss row showing an
"unknown" badge next to a known value (UI).

Open items: replace curated summaries with original official documents; add KB coverage for smishing,
crypto, data-breach and romance scams; rerun the evaluation with a larger, independently labelled dataset.

## Final hardening (2026-10-02)

| Area | Result |
|---|---|
| Knowledge base | 2 official texts added (CERT-In booklet, NCRP safety tips; fetched by script, provenance + SHA-256, not committed) and 4 team-written summaries (smishing, ransomware, romance/crypto, data breach/identity theft/account takeover): 16 documents / 69 chunks in pgvector |
| Complaint hallucination | Deterministic sentence-level validator + 14 regression tests (incl. the exact real-model sentences) |
| Docker | `docker compose up -d --build` on fresh volumes: migrations, model download, ingestion in-container, full demo via the browser |
| Retrieval | Re-measured without LLM: 17/19 hit@3, 11/19 hit@1 |
| Security | No secrets/`.env`/official texts tracked; no user text or keys in container logs; KB URLs http(s) only; 0 injection-like lines in official texts |

## Novelty modules (2026-10-02)

Baseline tagged `v1.0-baseline` before any change. Added one at a time without changing the RAG, database
or pipeline stages:

| Module | Backend | Frontend | Tests |
|---|---|---|---|
| Lookalike-URL analyser (rule-based, offline) | `services/scamcheck/url_analyzer.py`, `POST /api/v1/check/url` | `/check?mode=url` | `tests/unit/test_url_analyzer.py` |
| Red-flag highlighting (rule-based; LLM may only reword explanations) | `services/scamcheck/red_flags.py`, `POST /api/v1/check/message`, `red_flags` on chat results | `/check`, Analysis tab | `tests/unit/test_red_flags.py`, `tests/integration/test_scamcheck_api.py` |
| Evidence integrity kit (rule-based, client-side hashing) | `services/evidence/manifest.py`, `POST /api/v1/evidence/manifest` and `/verify`, `evidence_files` on complaint requests → Annexure A | Evidence tab kit (`EvidenceKit.tsx`, `lib/evidence.ts`) | `tests/unit/test_evidence_manifest.py`, `tests/integration/test_evidence_api.py` |
| English / Hindi replies | `services/language.py`, `language` on chat messages, Hindi evidence-deletion guard, localised fallback replies | reply-language selector | `tests/unit/test_language.py` |

Tamil was left out for now. Not done: measuring the rules or the Hindi output against a labelled dataset.
