# Demo script (≈6 minutes)

**Before the demo:** `docker compose up -d db`, `alembic upgrade head`, `python -m scripts.ingest_kb`,
start backend and frontend (see README). For the best output set `LLM_PROVIDER=openai` or `anthropic`
with a key; without one the app runs in clearly labelled *offline mock* mode.

## 1. Dashboard (30 s)
- Open http://localhost:3000. Point out system status: backend online, AI provider, **knowledge chunks indexed** (proves RAG data is loaded), the pipeline strip.

## 2. Report the incident (2 min)
- Click **Report Incident** and paste:
  > I received a WhatsApp message claiming to be from my bank. It asked me to click a link and enter my OTP because my account would otherwise be blocked.
- Watch the stage bar: *Analyzing → Extracting → Classifying → Retrieving sources → Generating → Saving*. These are server-sent events emitted as each backend step starts.
- **Analysis tab:** classification *Phishing* with confidence and alternative (*OTP scam*); incident summary shows Platform = WhatsApp marked **inferred**, and Date/Loss/Evidence marked **unknown** — nothing invented.
- Explanation with warning signs, immediate actions, reporting guidance and "Do not" list, with "Grounded in [S1]…" references.

## 3. Missing information follow-up (1 min)
- The assistant asked only about missing facts. Reply:
  > It happened yesterday evening. I didn't share the OTP and lost no money. I have screenshots.
- Summary updates in place (same incident): date filled, financial loss = No, evidence = Screenshots.

## 4. Sources (30 s)
- **Sources tab:** titles, organisations (I4C, RBI, NPCI…), document type, relevance score, expandable excerpt, official link.

## 5. Evidence checklist (30 s)
- Click **Evidence Checklist**: prioritised items, screenshots already ticked.

## 6. Complaint draft (1 min)
- **Complaint tab** → optionally enter a name → **Generate draft**. Show filled facts vs `[PLACEHOLDERS]` and the live "N placeholders to fill" counter as you edit. Copy / download.

## 7. Awareness (30 s)
- Click **Cyber Safety Tips**: personalised warning signs, prevention, precautions, and resources restricted to retrieved sources.

## 8. Engineering talking points
- Pipeline split into services (`extraction → classification → retrieval → generation → persistence`), prompts in `services/ai/prompts/`.
- Pydantic-validated structured outputs with one repair retry and safe fallbacks (tests feed malformed JSON).
- Regex grounding removes hallucinated phone numbers/URLs/amounts.
- pgvector cosine search; prompt-injection filtering of retrieved text.
- 40+ automated tests run without API keys or Docker.
