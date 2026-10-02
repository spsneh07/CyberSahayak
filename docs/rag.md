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
  → collapse to one citation per document (extra chunks of the same document are appended)
  → citations [S1..Sn] → prompts inside <sources> tags
```

Run ingestion (idempotent; unchanged files are skipped by content hash, deleted files are pruned):

```bash
cd backend && python -m scripts.ingest_kb
```

## Metadata stored

`title, organization, url (http/https only), category, published_date, document_type, source_note,
source_path, content_hash, embedding_identity`. `document_type` + `source_note` are required at ingestion
so every document states what it is. Every citation shown in the UI carries title, organisation, URL,
document type, provenance note and similarity score.

## Embeddings

| Provider | Kind | Needs |
|---|---|---|
| `hash` | Lexical: feature-hashed words + bigrams, 384-d, L2-normalised. Real vectors and real cosine search, but **no semantic understanding**. | nothing |
| `local` | **Semantic**: sentence-transformers `all-MiniLM-L6-v2` (384-d, normalised), CPU | `requirements-ml.txt` (~1 GB with CPU torch), model download ~90 MB on first use |
| `openai` | Semantic: any OpenAI-compatible `/embeddings` endpoint with `dimensions=384` | API key |

`EMBEDDING_DIM` must match the `vector(384)` column (migration `0001`).

**Consistency guard.** Each document stores the `embedding_identity` (`provider:model:dim`) used for its
vectors, and that identity is part of the ingestion content hash. Switching provider/model therefore
re-embeds every document on the next ingestion, and a query made with a different model than the index is
refused with `embedding_mismatch` instead of silently returning meaningless matches.

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

Two kinds of document, always distinguishable in metadata and in the UI:

| Kind | `document_type` | Count (2026-10-02) | Chunks | Source note shown to users |
|---|---|---|---|---|
| Team-written summaries | `curated_summary` | 14 | 31 | "Team-written summary … Not the official text; verify details at the source URL." |
| Official texts (CERT-In booklet, NCRP safety tips) | `official_text` | 2 | 38 | "Official document published by …, downloaded from <URL> on <date> (sha256 …). Text extracted automatically; verify against the original." |

Official texts are fetched with `python -m scripts.fetch_official_kb` (manifest:
`knowledge_base/official_sources.json`) and ingested locally; they are not committed to the repository.
Their category is `general` (they cover many topics). See `knowledge_base/README.md`.

## Validation on PostgreSQL + pgvector (2026-10-02)

Setup: `pgvector/pgvector:pg16` (pgvector 0.8.7), `vector(384)` + HNSW cosine index, 10 documents → 21
chunks, embeddings `local:sentence-transformers/all-MiniLM-L6-v2:384` (all stored vectors have norm 1.0).
Top-3 documents per query (cosine similarity):

| Query | S1 | S2 | S3 |
|---|---|---|---|
| bank message, click link, share OTP, account blocked | **phishing** 0.594 | upi_fraud 0.480 | banking_fraud 0.442 |
| buyer QR code, enter UPI PIN to receive, money deducted | **upi_fraud** 0.725 | shopping_fraud 0.493 | banking_fraud 0.355 |
| money debited via card transaction I never made | phishing 0.399 | **banking_fraud** 0.397 | upi_fraud 0.390 |
| is `sbi-kyc-update.xyz/login` safe, asks net-banking password | **phishing** 0.468 | upi_fraud 0.412 | banking_fraud 0.398 |
| fake Instagram profile with my photos asking friends for money | **social_media_impersonation** 0.683 | shopping_fraud 0.425 | phishing 0.394 |

Observations: the most relevant document is first in 4/5 queries and second (0.002 behind) for the
banking query. The fake-website guidance (inside the shopping document) is not retrieved for the
suspicious-URL query. Before the per-document collapse, the same document appeared up to twice in the
top 3; it now appears once. The dataset-level retrieval metric is in `docs/project_explanation.md`.

With the real LLM on the demo message, the explanation cited `[S1]` and the chat reply referred to S1 and
S6 — all ids that were actually retrieved — and the guidance's
reporting channels (1930 helpline, cybercrime.gov.in, RBI three-working-day reporting) all occur in the
retrieved excerpts (NCRP and RBI summaries).

## Retrieval re-measured after expanding the knowledge base (2026-10-02)

`python -m evaluation.run_eval --mode real --retrieval-only` — no LLM calls; 16 documents / 69 chunks;
`local:all-MiniLM-L6-v2`; top-3 documents; `RAG_MIN_SCORE=0.25`. Relevance = the document's topic category
is listed for the case (official texts are `general` and never count as hits, although they appeared in the
top 3 for 14/20 cases). The relevance labels were extended for the new topic documents, so this is **not
directly comparable** with the earlier 15/18 (old KB, old labels).

| Metric | Result |
|---|---|
| Cases with a relevant topic document | 19 |
| Relevant topic document ranked 1st | 11/19 |
| Relevant topic document in top 3 | 17/19 |

Misses: e06 online-shopping fraud (vishing/UPI/official booklet retrieved) and e17 crypto exchange scam
(only two documents above the score threshold, neither relevant). Raw output:
`backend/evaluation/results_retrieval.json`.
