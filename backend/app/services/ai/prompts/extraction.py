from app.schemas.incident import IncidentData
from app.services.ai.prompts.common import SAFETY_RULES, input_block

TASK = "extraction"

SYSTEM = f"""{SAFETY_RULES}

Task: extract a structured cybercrime incident record from the user's own words.
Rules:
- Copy identifiers (phone numbers, emails, URLs, UPI IDs, account/transaction numbers) EXACTLY as written. Do not guess or complete them.
- date_time: only if the user stated a date/time; keep their wording (e.g. "yesterday evening").
- financial_loss: true only if the user says money was lost/debited; false only if they say none was lost; otherwise null.
- amount/currency: only if stated. "Rs", "₹", "rupees" -> INR.
- evidence_available: things the user says they have (screenshots, SMS, call log, bank statement...).
- actions_taken: what the user says they already did (blocked card, called bank, reported...).
- field_sources: for each non-empty field, "user_provided" if stated explicitly, "inferred" if you inferred it (e.g. platform from "WhatsApp message").
- missing_information: short names of important unknown facts (e.g. "date_time", "amount", "transaction_id", "suspect_contact").
- incident_type/subtype: a short provisional guess or null (classification happens separately).
- confidence: 0-1, how complete and clear the description is.
If <input> includes previous_incident, return the UPDATED full record: keep previous facts and add new ones from the new message."""


def build(message: str, previous: IncidentData | None) -> str:
    payload: dict = {"user_message": message}
    if previous is not None:
        payload["previous_incident"] = previous.model_dump(mode="json", exclude={"missing_information"})
    return input_block(payload)
