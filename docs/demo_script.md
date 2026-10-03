# Demo script (≈6 minutes)

**Before the demo:** start Docker Desktop, `docker compose up -d db`, `alembic upgrade head`,
`python -m scripts.ingest_kb`, start backend and frontend (see README). Check http://localhost:8000/health
shows `"database": "postgresql"` and the expected `knowledge_embedding`.

Real mode (validated): Groq `openai/gpt-oss-120b` or `openai/gpt-oss-20b` + local `all-MiniLM-L6-v2` (the web-UI run used 20b; each analysed turn took about a minute). **Timing:** each analysed
message makes ~5–6 LLM calls; on Groq's free tier, rate limiting made turns take ~1–2 minutes during
validation (stage bar keeps moving; backend retries 429s). For a live presentation, run the demo once
beforehand, consider a paid/higher-limit key, or fall back to offline mock mode (`LLM_PROVIDER=mock`,
clearly labelled in the UI). Wording of real-LLM answers varies between runs.

**Docker option (validated 2026-10-02):** `docker compose up -d --build`, then
`docker compose exec backend python -m scripts.ingest_kb` (after `python -m scripts.fetch_official_kb` on
the host). The full demo below was run through the containers on fresh volumes.

## 1. Dashboard (30 s)
- Open http://localhost:3000. Point out system status: backend online, AI provider, **knowledge chunks indexed** (proves RAG data is loaded), the pipeline strip.

## 2. Report the incident (2 min)
- Click **Report Incident** and paste:
  > I received a WhatsApp message claiming to be from my bank. It asked me to click a link and enter my OTP because my account would otherwise be blocked.
- Watch the stage bar: *Analyzing → Extracting → Classifying → Retrieving sources → Generating → Saving*. These are server-sent events emitted as each backend step starts.
- **Analysis tab:** classification *Phishing* (real run: 0.92, alternatives OTP scam / smishing / vishing, with reasoning citing the message details); incident summary shows Platform = WhatsApp marked **inferred**, and Date/Loss/Evidence marked **unknown** — nothing invented.
- Explanation with warning signs, immediate actions, reporting guidance and "Do not" list, with "Grounded in [S1]…" references.

## 3. Missing information follow-up (1 min)
- The assistant asked only about missing facts. Reply:
  > It happened yesterday evening. I didn't share the OTP and lost no money. I have screenshots.
- Summary updates in place (same incident): date filled, financial loss = No, evidence = Screenshots.

## 4. Sources (30 s)
- **Sources tab:** titles, organisations (I4C, RBI, NPCI…), document type, relevance score, expandable excerpt, official link, and the provenance note ("Team-written summary … Not the official text"). Each document appears once.

## 5. Evidence checklist (30 s)
- Click **Evidence Checklist**: prioritised items, screenshots already ticked.

## 6. Complaint draft (1 min)
- Point out: the narrative is checked sentence by sentence against the incident record; unsupported claims
  (e.g. "I have not taken any action") are removed and missing values stay as placeholders.
- **Complaint tab** → optionally enter a name → **Generate draft**. Show filled facts vs `[PLACEHOLDERS]` and the live "N placeholders to fill" counter as you edit. Copy / download.

## 7. Awareness (30 s)
- Resources come only from retrieved sources; in the Docker run they included the official CERT-In booklet.
- Click **Cyber Safety Tips**: personalised warning signs, prevention, precautions, and resources restricted to retrieved sources.

## 8. Novelties (1.5 min)
- **Check a suspicious message** (nav → *Check message / link*, "use sample"): each red flag is
  highlighted in place with its category and explanation. Say clearly that these come from fixed rules,
  not AI; the optional checkbox only lets the model reword explanations.
- **Check a link** (tab *Link (URL)*, sample `https://hdfcbank.com.secure-login.top/verify`): registered
  domain `secure-login.top`, "hdfc in the subdomain" (high), unusual TLD, phishing path word. Then try
  `https://www.hdfcbank.com` (low, official) and an unfamiliar site such as `https://www.my-local-bakery.in`
  (low, no indicators) to show that unfamiliar is not the same as malicious. The URL is never opened.
- **Hindi**: on `/assistant`, set *Reply language* to हिन्दी and report a Hinglish incident, e.g.
  > Mujhe WhatsApp par +91 98765 43210 se message aaya ki mera SBI account block ho jayega, link http://sbi-kyc-update.xyz/login par OTP daalo. Maine OTP daal diya aur Rs 15,000 kat gaye.

  Guidance comes back in Hindi, while the phone number, link and amount stay exactly as typed and the
  citations [S1]… still point to retrieved sources. The complaint draft stays in English with its
  placeholders. On Groq's free tier this turn can take a couple of minutes (rate limits); if the model
  is unavailable the fixed fallback reply is shown in Hindi.

- **Evidence integrity kit** (Evidence tab): add a screenshot and a PDF; each gets a SHA-256 fingerprint
  computed in the browser (point out that nothing is uploaded). Link one to a checklist item, then
  **Create & download manifest**. Under *Verify a file*, re-select the same file under another name
  (match, rename noted) and an edited copy (no match). Generate the complaint: the files and
  fingerprints appear as **Annexure A**. Say what it does not prove: that the content is genuine.

## 9. Engineering talking points
- Pipeline split into services (`extraction → classification → retrieval → generation → persistence`), prompts in `services/ai/prompts/`.
- Pydantic-validated structured outputs with one repair retry and safe fallbacks (tests feed malformed JSON).
- Regex grounding removes hallucinated phone numbers/URLs/amounts.
- pgvector cosine search; prompt-injection filtering of retrieved text.
- Tests split into unit / offline integration / PostgreSQL+pgvector / real-provider suites.
- Deterministic guards: no invented identifiers, no unsupported helplines/URLs, no evidence-deletion advice.
