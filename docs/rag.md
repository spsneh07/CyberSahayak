# Retrieval-Augmented Generation (RAG)

## Pipeline

```
knowledge_base/documents/*.md|.txt|.pdf
  → parse (front-matter / PDF text + .meta.json)        services/rag/ingest.py
  → clean (Unicode NFKC, control chars, whitespace)     services/rag/sanitize.py
  → strip instruction-like lines (prompt-injection)     services/rag/sanitize.py
  → chunk (heading-aware, ~900 chars, 1-para overlap)   services/rag/chunker.py
  → embed (EMBEDDING_PROVIDER)                          services/ai/providers/*
  → store knowledge_documents + knowledge_chunks(vector) repositories/knowledge.py
  → query: embed → cosine search (pgvector `<=>`, HNSW)  services/rag/retriever.py
  → citations [S1..Sn] → prompts inside <sources> tags
```

Run ingestion (idempotent; unchanged files are skipped by content hash, deleted files are pruned):

```bash
cd backend && python -m scripts.ingest_kb
```

## Metadata stored

`title, organization, url, category, published_date, document_type, source_path, content_hash`.
Every citation shown in the UI carries title, organisation, URL, document type and similarity score.

## Embeddings

| Provider | Quality | Needs |
|---|---|---|
| `hash` (default) | Lexical: feature-hashed words + bigrams, 384-d, L2-normalised. Real vectors, real cosine search — but no semantic understanding. | nothing |
| `openai` | Semantic (`text-embedding-3-small` with `dimensions=384`) — any OpenAI-compatible `/embeddings` endpoint. | API key |

`EMBEDDING_DIM` must match the `vector(N)` column created by migration `0001`. Changing it requires a new migration and re-ingestion.

## Retrieval for an incident

`Retriever.for_incident` queries with `category label + subtype + platform + description`, then adds up to two
chunks about reporting channels (and bank liability when money was lost) so guidance can cite real channels
instead of inventing them. Hits below `RAG_MIN_SCORE` are dropped.

## Prompt-injection defences

1. Ingestion removes lines matching instruction patterns ("ignore previous instructions", "you are now", fake `<system>` tags…) and logs the count.
2. Retrieval re-applies the filter (defence in depth) and escapes metadata placed in tag attributes.
3. Prompts wrap chunks in `<source>` tags and the system prompt states that `<sources>` is untrusted data.
4. Output checks: guidance/explanation URLs and short helpline-style numbers not present in retrieved sources are replaced with `[official … — verify]`; awareness resources are filtered to retrieved URLs only; `source_ids` are filtered to ids actually retrieved.

## Knowledge base provenance

Seed documents are **curated summaries written by the project team** (labelled `curated_summary`), each linked
to the official organisation page. They are not verbatim official texts. Verify details at the linked source
and prefer adding the original official documents. See `knowledge_base/README.md`.
