from app.schemas.incident import IncidentData
from app.services.ai.prompts.common import SAFETY_RULES, input_block
from app.services.classification.taxonomy import taxonomy_for_prompt

TASK = "classification"

SYSTEM = f"""{SAFETY_RULES}

Task: classify the incident into exactly ONE category id from this taxonomy:
{taxonomy_for_prompt()}

Rules:
- Pick the category describing the core fraud mechanism (e.g. a WhatsApp message with a fake bank link asking for an OTP is "phishing"; list "otp_scam" as an alternative).
- subtype: short free-text refinement (e.g. "bank impersonation via WhatsApp").
- confidence: 0-1. If the description is too vague, use "unknown" with low confidence.
- reasoning: 1-3 sentences citing the specific details from the incident that support the choice.
- alternatives: up to 3 other plausible categories with confidence."""


def build(incident: IncidentData) -> str:
    return input_block({"incident": incident.model_dump(mode="json", exclude={"field_sources"})})
