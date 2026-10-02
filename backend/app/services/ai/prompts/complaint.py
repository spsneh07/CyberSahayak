from app.schemas.classification import ClassificationResult
from app.schemas.incident import IncidentData
from app.services.ai.prompts.common import SAFETY_RULES, input_block

TASK = "complaint"

SYSTEM = f"""{SAFETY_RULES}

Task: write the "Incident description" paragraph of a formal cybercrime complaint, in first person, formal tone.
- Use ONLY facts in <input>. For any fact a complaint would normally include but which is missing, write a bracketed placeholder such as [DATE], [TIME], [AMOUNT], [TRANSACTION ID], [SUSPECT PHONE NUMBER].
- Do not add legal sections, conclusions about guilt, or facts not provided.
- requested_assistance: 2-4 short formal requests appropriate to this incident (e.g. investigate, help freeze/recover funds if money was lost, take down fake profile/website)."""


def build(incident: IncidentData, classification: ClassificationResult | None) -> str:
    return input_block({
        "incident": incident.model_dump(mode="json", exclude={"field_sources"}),
        "classification": classification.model_dump() if classification else None,
    })
