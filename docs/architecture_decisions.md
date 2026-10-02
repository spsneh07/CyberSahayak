# Architecture Decision Records

### ADR-1 Monolith FastAPI + Next.js
A single backend service and a single frontend. A course project does not
benefit from microservices; module boundaries live in `services/`.

### ADR-2 PostgreSQL + pgvector for both relational and vector data
One database, transactional consistency between incidents and knowledge chunks,
no extra vector DB to run. Cosine distance (`<=>`) with an HNSW index.
Tests use SQLite; the knowledge repository falls back to in-Python cosine
similarity when the dialect is not PostgreSQL. This keeps tests key-free and
Docker-free while production uses real pgvector.

### ADR-3 Provider abstraction via plain `httpx`
`LLMProvider.complete(system, user, json_schema)` and `EmbeddingProvider.embed(texts)`.
Implementations: `mock`, `openai` (any OpenAI-compatible endpoint: OpenAI, Groq,
OpenRouter, Ollama, LM Studio), `anthropic`. No vendor SDKs → fewer dependencies.
Embedding providers: `hash` (deterministic local feature-hashing; offline,
lexical-quality), `openai`-compatible. Vector dimension is fixed by
`EMBEDDING_DIM` and the migration.

### ADR-4 Structured outputs validated by Pydantic, with one repair retry
LLM is asked for JSON matching the schema; we strip fences, parse, validate.
On failure we retry once with the validation error; then raise
`StructuredOutputError`, which callers turn into a safe fallback (e.g. category
`unknown`) instead of a 500.

### ADR-5 Deterministic where facts matter
Phone numbers, emails, URLs, UPI IDs and amounts are also extracted with
regexes and merged; anything the LLM returns that is not grounded in the user
text is dropped for identifier fields. The complaint is a template filled from
validated fields; missing values remain `[PLACEHOLDER]`. The LLM only writes the
narrative paragraph, constrained to supplied facts.

### ADR-6 Retrieved text is data
Chunks are injected inside `<source id=…>` delimiters with an explicit
instruction that they are untrusted reference material; lines matching common
injection patterns are removed during ingestion and retrieval.

### ADR-7 SSE for genuine pipeline progress
`POST /conversations/{id}/messages/stream` emits a `stage` event as each
pipeline step actually starts, then a `result` event. UI states are therefore
real, not timers.

### ADR-8 Knowledge base = curated summaries with real source URLs
No network crawling at build time. The seed KB consists of short summaries we
wrote of public guidance, each linked to the official page it summarises and
labelled `document_type: curated_summary`. Users should verify and can add
original documents (`.md`, `.txt`, `.pdf`) to `knowledge_base/` and re-ingest.

### ADR-9 No auth in v1
`users` table exists; conversations are anonymous by id until the core pipeline is complete.
