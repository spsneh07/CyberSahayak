"""Incident extraction: LLM structured output, grounded and merged with regex identifiers."""
import logging

from app.schemas.incident import FactSource, IncidentData
from app.services.ai.base import LLMProvider, StructuredOutputError
from app.services.ai.prompts import extraction as prompt
from app.services.ai.structured import generate_structured
from app.services.incident.identifiers import extract_identifiers, grounded

log = logging.getLogger(__name__)

ID_FIELDS = ("phone_numbers", "emails", "urls", "upi_ids", "account_identifiers")

# Importance-ordered facts and the question we ask when they are unknown.
QUESTIONS: dict[str, str] = {
    "date_time": "When did this happen (date and approximate time)?",
    "platform": "Where were you contacted — WhatsApp, SMS, phone call, email, a website or an app?",
    "financial_loss": "Did you lose any money or share any banking details/OTP?",
    "amount": "How much money was lost, and in what currency?",
    "transaction_id": "Do you have the transaction ID / UTR number of the payment?",
    "suspect_contact": "Do you have the phone number, profile, UPI ID, email or link the suspect used?",
    "evidence": "Have you saved screenshots or the original messages?",
}


def compute_missing(data: IncidentData) -> list[str]:
    missing: list[str] = []
    if not data.date_time:
        missing.append("date_time")
    if not data.platform:
        missing.append("platform")
    if data.financial_loss is None:
        missing.append("financial_loss")
    if data.financial_loss and data.amount is None:
        missing.append("amount")
    if data.financial_loss and not data.account_identifiers:
        missing.append("transaction_id")
    if not any(getattr(data, f) for f in ("phone_numbers", "emails", "urls", "upi_ids")):
        missing.append("suspect_contact")
    if not data.evidence_available:
        missing.append("evidence")
    return missing


def follow_up_questions(missing: list[str], limit: int = 3) -> list[str]:
    return [QUESTIONS[m] for m in missing if m in QUESTIONS][:limit]


class IncidentExtractor:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def extract(self, message: str, previous: IncidentData | None = None) -> tuple[IncidentData, list[str]]:
        """Return (validated incident, warnings)."""
        warnings: list[str] = []
        user_text = ((previous.description + "\n") if previous else "") + message
        try:
            data = generate_structured(
                self.llm, task=prompt.TASK, system=prompt.SYSTEM,
                user=prompt.build(message, previous), schema=IncidentData,
            )
        except StructuredOutputError:
            log.warning("extraction failed; using deterministic fallback")
            warnings.append("AI extraction failed; identifiers were extracted with rule-based parsing only.")
            data = previous.model_copy(deep=True) if previous else IncidentData()
            data.description = user_text.strip()

        self._ground(data, user_text, previous)
        if previous:
            self._keep_previous_facts(data, previous)
        data.missing_information = compute_missing(data)
        return data, warnings

    @staticmethod
    def _ground(data: IncidentData, text: str, previous: IncidentData | None) -> None:
        """Drop identifiers the model invented; add ones the regexes found."""
        found = extract_identifiers(text)
        for f in ID_FIELDS:
            kept = grounded(getattr(data, f), text)
            for v in getattr(found, f):
                if v not in kept:
                    kept.append(v)
            setattr(data, f, kept)
            if kept:
                data.field_sources.setdefault(f, FactSource.user_provided)
        if data.amount is None and found.amount is not None:
            data.amount, data.currency = found.amount, found.currency
            data.field_sources["amount"] = FactSource.user_provided
        if data.amount is not None and found.amount is None and not (previous and previous.amount == data.amount):
            # An amount that never appears in the text is an invention.
            if str(int(data.amount)) not in text.replace(",", ""):
                data.amount, data.currency = None, None
        if data.amount is not None and data.financial_loss is None:
            data.financial_loss = True
            data.field_sources.setdefault("financial_loss", FactSource.inferred)
        if not data.description:
            data.description = text.strip()

    @staticmethod
    def _keep_previous_facts(data: IncidentData, previous: IncidentData) -> None:
        for name in IncidentData.model_fields:
            if name in ("missing_information", "confidence", "description", "field_sources"):
                continue
            old, new = getattr(previous, name), getattr(data, name)
            if isinstance(old, list):
                setattr(data, name, old + [x for x in new if x not in old])
            elif new in (None, "") and old not in (None, ""):
                setattr(data, name, old)
        for k, v in previous.field_sources.items():
            data.field_sources.setdefault(k, v)
        if len(previous.description) > len(data.description):
            data.description = previous.description
