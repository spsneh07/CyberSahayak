from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation
from app.schemas.incident import IncidentData
from app.services.ai.prompts.common import SAFETY_RULES, input_block, sources_block

TASK = "explanation"

SYSTEM = f"""{SAFETY_RULES}

Task: explain to the victim what likely happened.
- summary: 1-2 sentences restating the incident in plain words (only stated facts).
- why_this_type: why it resembles the classified type, referring to specific details.
- warning_signs: the red flags present in THIS incident.
- simple_explanation: how this kind of scam works, for a non-technical reader (3-5 sentences).
- source_ids: ids of <sources> you relied on (may be empty)."""


def build(incident: IncidentData, classification: ClassificationResult, sources: list[Citation]) -> str:
    return (
        input_block({
            "incident": incident.model_dump(mode="json", exclude={"field_sources"}),
            "classification": classification.model_dump(),
        })
        + "\n"
        + sources_block(sources)
    )
