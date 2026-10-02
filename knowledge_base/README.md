# Knowledge base

Documents in `documents/` are ingested by `python -m scripts.ingest_kb` (from `backend/`).

## Format

Markdown or text with a front-matter header:

```
---
title: ...                # required
organization: ...         # required — the organisation whose guidance this is
url: https://...          # required, http(s) only — the official page the content is based on
category: phishing | upi_fraud | ... | general | reporting | evidence   # required
date: 2017-07-06          # publication date of the underlying guidance if known, otherwise empty
document_type: curated_summary | advisory | circular | faq | official_text   # required
source_note: ...          # required — plain statement of provenance, shown to users with the citation
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

## Current contents

10 documents, all `document_type: curated_summary`, each with
`source_note: Team-written summary of public guidance from the organisation above. Not the official text;
verify details at the source URL.` Source URLs point to organisation home pages (cybercrime.gov.in,
rbi.org.in, npci.org.in, cert-in.org.in, sancharsaathi.gov.in), not to specific official documents.
Only the RBI document has a date (the July 2017 customer-liability directions it summarises).
