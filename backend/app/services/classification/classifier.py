import logging

from app.schemas.classification import AlternativeCategory, ClassificationResult
from app.schemas.incident import IncidentData
from app.services.ai.base import LLMProvider, StructuredOutputError
from app.services.ai.prompts import classification as prompt
from app.services.ai.structured import generate_structured

log = logging.getLogger(__name__)

MIN_CONFIDENCE = 0.35


class IncidentClassifier:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def classify(self, incident: IncidentData) -> ClassificationResult:
        try:
            result = generate_structured(
                self.llm, task=prompt.TASK, system=prompt.SYSTEM,
                user=prompt.build(incident), schema=ClassificationResult,
            )
        except StructuredOutputError:
            log.warning("classification failed; returning unknown")
            return ClassificationResult(
                category="unknown", confidence=0.0,
                reasoning="The classifier could not produce a valid result. More information is needed.",
            )
        result.alternatives = [a for a in result.alternatives if a.category != result.category][:3]
        if result.category != "unknown" and result.confidence < MIN_CONFIDENCE:
            # Too uncertain to label — surface the guess as an alternative instead.
            result.alternatives.insert(0, AlternativeCategory(category=result.category, confidence=result.confidence))
            result.category, result.subtype = "unknown", None
            result.reasoning = f"Low confidence. {result.reasoning}".strip()
        return result
