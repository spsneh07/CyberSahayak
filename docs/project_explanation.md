# Project explanation (for viva / report)

**Course:** 21CSE306P Applied Generative AI — B.Tech 5th semester, 2026-27
**Project:** AI Cyber Crime Complaint & Awareness Assistant

## Problem
Victims of cybercrime struggle to recognise the scam, know what to do first, preserve evidence and write a
formal complaint. Official guidance exists but is scattered and hard for non-technical users to apply.

## Solution
A conversational GenAI assistant that turns a free-text description into: a structured incident record,
a cybercrime classification with confidence and reasoning, a plain-language explanation, grounded
response guidance and evidence checklist, an editable complaint draft, and personalised awareness content.

## Where Generative AI is used (and where it is deliberately not)

| Step | GenAI? | Why |
|---|---|---|
| Intent detection | LLM, structured | flexible understanding of messages |
| Extraction | LLM, structured + regex grounding | LLM understands context; regex guarantees identifiers are real |
| Classification | LLM against a fixed 21-class taxonomy | reasoning + alternatives; validated enum |
| Retrieval | Embeddings + pgvector | grounds answers in trusted documents |
| Explanation / guidance / awareness | LLM with retrieved sources | personalised, plain-language |
| Complaint | Template + LLM narrative only | formal structure must be reliable; facts never invented |

## Key GenAI concepts demonstrated
- **Prompt engineering:** role + rules + task-specific instructions; inputs passed as JSON data blocks.
- **Structured output:** JSON Schema from Pydantic models; validation, repair retry, fallbacks.
- **RAG:** chunking, embeddings, vector similarity, citation of sources.
- **Hallucination control:** grounding identifiers in user text, scrubbing unsupported URLs/helplines, placeholders.
- **Prompt-injection defence:** retrieved text treated as data, filtered, delimited.
- **Provider abstraction:** swap OpenAI-compatible / Anthropic / offline mock via environment variables.

## Evaluation

### Dataset
`backend/evaluation/dataset.jsonl` — **20 fictional cases written by the project team**: one or two per
category (phishing ×2, smishing, vishing, UPI fraud, banking fraud, shopping fraud, investment scam, job
scam, identity theft, account takeover, social-media impersonation, malware, ransomware, sextortion,
cyberbullying, romance scam, crypto scam, data theft, and one deliberately vague case expecting
`unknown`). 8 cases carry expected identifiers/amounts (10 fields in total). Each case lists which
knowledge-base categories are relevant to it; 18 have at least one relevant KB document.

### Method (`python -m evaluation.run_eval --mode real`)
| Metric | How it is computed |
|---|---|
| Classification exact / acceptable | predicted category = expected; "acceptable" also allows listed alternatives |
| Identifier fields | expected phone/email/URL/UPI values ⊆ extracted values (normalised); amount equality |
| Retrieval hit@3 | at least one of the top-3 retrieved documents has a relevant KB category |
| Unsupported contacts | URLs / 3–6-digit helpline-style numbers in the **raw** guidance output that do not occur in the retrieved excerpts (measured before the scrubbing guard) |
| Invalid source ids | cited ids not among the retrieved ids |
| Evidence-deletion advice | raw guidance items flagged by the safety filter (before it removes them) |
| Complaint completeness | every user-provided fact (date/time, platform, identifiers, amount) appears in the draft; no phone/email/UPI identifiers that the user did not provide |

### Measured result — real mode (run 2026-10-02, 993 s)
LLM `openai/gpt-oss-120b` via Groq · embeddings `local:sentence-transformers/all-MiniLM-L6-v2:384` ·
PostgreSQL 16 + pgvector 0.8.7. Raw output: `backend/evaluation/results_real.json`.

| Metric | Result |
|---|---|
| Classification exact | 20/20 |
| Classification acceptable | 20/20 |
| Identifier fields correct | 10/10 |
| Retrieval hit@3 | 15/18 |
| Guidance outputs with an unsupported contact (raw) | 1/19 |
| Guidance outputs with invalid source ids | 0/19 |
| Guidance outputs advising evidence deletion (raw) | 2/19 |
| Complaints containing all provided facts | 19/19 |
| Complaints with invented identifiers | 0/19 |

Details behind the non-perfect rows (from the raw results):
- Retrieval misses: e02 smishing (electricity-bill SMS → banking/vishing/reporting docs), e17 crypto
  (relevant investment-scam guidance not retrieved), e20 data breach (CERT-In doc not retrieved).
- Unsupported contact: e15 cyberbullying — the model suggested the 1930 financial-fraud helpline, which was
  not in the retrieved excerpts (the scrubber replaces it with "[official helpline — verify]").
- Evidence-deletion advice: e07 ("…before deleting anything") and e12 (factory reset after backing up);
  both removed by the safety filter. The filter is deliberately conservative.

**How to read this.** 20 short, unambiguous, team-written cases cannot establish real-world accuracy;
the classification score mostly shows the model follows the taxonomy on clear descriptions. The guard
metrics show why the deterministic output checks are needed. Results are for one run of one model;
wording and occasionally labels vary between runs.

The **offline/mock** mode scores are intentionally not reported: the mock's keyword rules were written
alongside this dataset.

### Real-provider integration tests
`RUN_REAL_PROVIDER_TESTS=1 pytest tests/real_provider` — 2 passed on 2026-10-02 with
`openai/gpt-oss-20b` (Groq). They were run on the 20b model because the evaluation exhausted the
120b model's free-tier daily token quota (200,000 tokens/day; HTTP 429 "tokens per day").

### Qualitative observations (not measured)
From manual end-to-end runs (120b via script, 20b via the web UI):
- Extraction kept unknowns unknown; follow-up details merged into the same incident and only the remaining
  gap (suspect contact) was asked.
- Complaint drafts used the stated date verbatim after the prompt fix, but the 20b model still wrote
  "I have not yet taken any action to report the incident" once, despite the prompt rule (unknown ≠ none),
  and described the sender as "a contact". Users must review drafts.
- Some guidance items are generic or slightly inaccurate (e.g. advising WhatsApp "end-to-end encryption
  settings").
- Retrieval returns marginally related documents in lower ranks (e.g. job-scam summary at 0.44 for the
  phishing demo).

## Limitations
See README → Limitations.
