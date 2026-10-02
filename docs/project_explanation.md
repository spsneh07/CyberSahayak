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
`backend/evaluation/dataset.jsonl` contains 20 fictional cases. `python -m evaluation.run_eval` measures
classification and identifier extraction for the configured provider and writes `results.json` with the
provider/model recorded. Report only numbers you obtained from a run. Note: the offline mock's keyword rules
and this dataset were written by the same team, so a mock score says nothing about real-world accuracy —
evaluate with a real LLM for the report.

## Limitations
See README → Limitations.
