# Knowledge base

Documents in `documents/` are ingested by `python -m scripts.ingest_kb` (from `backend/`).

## Format

Markdown or text with a front-matter header:

```
---
title: ...
organization: ...
url: https://...          # the official page the content is based on
category: phishing | upi_fraud | ... | general | reporting | evidence
date: 2017-07-06          # publication date if known, otherwise leave empty
document_type: curated_summary | advisory | circular | faq | official_text
---
```

PDFs are supported with a sidecar `<name>.meta.json` containing the same keys.

## Provenance — read this

The seed documents are **curated summaries written by the project team** of
publicly available guidance; they are *not* verbatim copies of the official
documents and are labelled `document_type: curated_summary`. Each links to the
official organisation page it is based on. Before relying on any detail
(helpline numbers, timelines, procedures) verify it at the linked source, and
prefer adding the original official documents here and re-running ingestion.
