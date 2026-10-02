from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation
from app.schemas.incident import IncidentData
from app.services.ai.prompts.common import SAFETY_RULES, input_block, sources_block

TASK = "awareness"

SYSTEM = f"""{SAFETY_RULES}

Task: create short personalised cyber-awareness content so the user can recognise and avoid this kind of scam in future.
- headline: one memorable line.
- warning_signs: how to spot this scam next time (generalised from the user's experience).
- prevention_tips: concrete habits/settings.
- future_precautions: longer-term protections.
- resources: ONLY items whose url appears in <sources> (title, organization, url). Never invent links.
If no incident is given, produce general awareness content for the topic in <input>."""


def build(incident: IncidentData | None, classification: ClassificationResult | None,
          sources: list[Citation], topic: str | None = None) -> str:
    return (
        input_block({
            "incident": incident.model_dump(mode="json", exclude={"field_sources"}) if incident else None,
            "classification": classification.model_dump() if classification else None,
            "topic": topic,
        })
        + "\n"
        + sources_block(sources)
    )
