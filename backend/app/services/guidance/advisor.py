"""Explanation + response guidance + evidence checklist, grounded in retrieved sources."""
import logging
import re

from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation, EvidenceChecklistItem, Explanation, Guidance
from app.schemas.incident import IncidentData
from app.services.ai.base import LLMProvider, StructuredOutputError
from app.services.ai.prompts import explanation as explanation_prompt
from app.services.ai.prompts import guidance as guidance_prompt
from app.services.ai.structured import generate_structured
from app.services.classification.taxonomy import CATEGORY_BY_ID
from app.services.guidance.safety import drop_evidence_destruction

log = logging.getLogger(__name__)

_URL = re.compile(r"https?://[^\s)\]]+|\bwww\.[^\s)\]]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:gov|nic|org|com)\.in\b|\b[a-z0-9-]+\.gov\.in\b", re.I)
_NUMBER = re.compile(r"(?<!\d)(?:\+?\d[\d\s-]{2,}\d)(?!\d)")

BASELINE_EVIDENCE = [
    EvidenceChecklistItem(item="Screenshots of all messages/chats showing date, time and sender", why="Shows how the incident happened", priority="high"),
    EvidenceChecklistItem(item="The original messages, emails and call logs (do not delete them)", why="Originals carry metadata investigators may need", priority="high"),
    EvidenceChecklistItem(item="A written timeline of events while it is fresh", why="Helps you give a consistent, complete complaint", priority="medium"),
]


def _source_text(sources: list[Citation]) -> str:
    return " ".join(f"{s.url} {s.excerpt}" for s in sources).lower()


def scrub_unsupported(text: str, sources: list[Citation]) -> str:
    """Remove URLs and phone-like numbers that are not present in retrieved sources."""
    allowed = _source_text(sources)

    def url_ok(m: re.Match[str]) -> str:
        u = m.group(0).rstrip(".,")
        core = re.sub(r"^https?://(www\.)?", "", u.lower()).rstrip("/")
        return m.group(0) if core and core.split("/")[0] in allowed else "[official website — verify]"

    def num_ok(m: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) < 3 or len(digits) > 6:  # only police/helpline-style short codes are risky; leave others
            return m.group(0)
        return m.group(0) if digits in re.sub(r"[^\d ]", " ", allowed).split() else "[official helpline — verify]"

    return _NUMBER.sub(num_ok, _URL.sub(url_ok, text))


class Advisor:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def explain(self, incident: IncidentData, cls: ClassificationResult, sources: list[Citation]) -> Explanation:
        try:
            exp = generate_structured(
                self.llm, task=explanation_prompt.TASK, system=explanation_prompt.SYSTEM,
                user=explanation_prompt.build(incident, cls, sources), schema=Explanation,
            )
        except StructuredOutputError:
            cat = CATEGORY_BY_ID.get(cls.category, CATEGORY_BY_ID["unknown"])
            return Explanation(summary=incident.description[:300], why_this_type=cls.reasoning,
                               simple_explanation=f"{cat.label}: {cat.definition}")
        valid_ids = {s.id for s in sources}
        exp.source_ids = [i for i in exp.source_ids if i in valid_ids]
        exp.simple_explanation = scrub_unsupported(exp.simple_explanation, sources)
        return exp

    def guide(self, incident: IncidentData, cls: ClassificationResult, sources: list[Citation]) -> Guidance:
        try:
            g = generate_structured(
                self.llm, task=guidance_prompt.TASK, system=guidance_prompt.SYSTEM,
                user=guidance_prompt.build(incident, cls, sources), schema=Guidance,
            )
        except StructuredOutputError:
            log.warning("guidance generation failed; using minimal safe guidance")
            g = Guidance(
                immediate_actions=["If money or banking details are involved, contact your bank immediately through its official channels."],
                reporting_guidance=["Report the incident through the official national cybercrime reporting channel or your local police station."],
            )
        for field in ("immediate_actions", "security_steps", "reporting_guidance", "do_not"):
            items = [scrub_unsupported(x, sources) for x in getattr(g, field)]
            setattr(g, field, items if field == "do_not" else drop_evidence_destruction(items))
        g.source_ids = [i for i in g.source_ids if i in {s.id for s in sources}]
        g.evidence_checklist = self.evidence_checklist(incident, g.evidence_checklist)
        return g

    @staticmethod
    def evidence_checklist(incident: IncidentData, generated: list[EvidenceChecklistItem]) -> list[EvidenceChecklistItem]:
        """Merge model items with a deterministic baseline and identifier-driven items."""
        items = list(generated)
        extra = list(BASELINE_EVIDENCE)
        if incident.financial_loss or incident.upi_ids or incident.account_identifiers:
            extra.append(EvidenceChecklistItem(item="Bank/UPI statement and transaction ID (UTR) for each payment", why="Needed to trace and hold funds", priority="high"))
        if incident.urls:
            extra.append(EvidenceChecklistItem(item=f"The suspicious link(s): {', '.join(incident.urls[:3])} (copy, don't open)", why="Allows the site to be investigated", priority="high"))
        if incident.phone_numbers:
            extra.append(EvidenceChecklistItem(item=f"Suspect phone number(s): {', '.join(incident.phone_numbers[:3])} and call log", why="Identifies the suspect", priority="high"))
        if incident.upi_ids:
            extra.append(EvidenceChecklistItem(item=f"Suspect UPI ID(s): {', '.join(incident.upi_ids[:3])}", why="Identifies the receiving account", priority="high"))
        existing = " ".join(i.item.lower() for i in items)
        for e in extra:
            key = e.item.lower().split()[0:3]
            if " ".join(key) not in existing:
                items.append(e)
        have = " ".join(incident.evidence_available).lower()
        for it in items:
            words = [w for w in re.findall(r"[a-z]{5,}", it.item.lower())]
            it.already_available = it.already_available or any(w in have for w in words)
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(items, key=lambda i: order[i.priority])[:10]
