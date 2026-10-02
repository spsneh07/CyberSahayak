"""Deterministic post-generation validation of the complaint narrative.

The narrative is compared sentence by sentence with the validated incident record and the user's own
words (`incident.description` holds the user's messages verbatim). Claims the record does not support are
removed or replaced by placeholders. The prompt asks the model not to make such claims; this module
enforces it.
"""
import re

from app.schemas.incident import IncidentData
from app.services.incident.identifiers import AMOUNT_RE, extract_identifiers

_NEG = re.compile(r"\b(not|no|never|none|nothing)\b|n't\b", re.I)

# Statements about what the complainant did / did not do after the incident.
_ACTION_CLAIM = re.compile(
    r"\b(no (further |other |additional )?(action|steps?|complaint)s?"
    r"|(not|n't|never) (yet )?(taken|take|reported|report|informed|inform|contacted|contact|approached|filed|file|lodged|done|notified|complained)"
    r"|(have|has|had) (already |also )?(reported|informed|contacted|called|approached|filed|blocked|lodged|complained|notified|visited|frozen|changed)"
    r"|(i|we) (already |also |immediately |then )?(reported|informed|contacted|called|approached|filed|blocked|lodged|complained|notified|visited|froze|changed))\b",
    re.I,
)
# Statements about money lost / not lost.
_LOSS_NEG = re.compile(
    r"\b(no (financial |monetary )?loss|no money|(not|n't|never) (lost|lose|been debited|been deducted|suffered)|lost no)\b", re.I)
_LOSS_POS = re.compile(r"\b(lost|debited|deducted|siphoned|withdrawn|transferred|paid)\b", re.I)
# Statements about what the complainant shared / entered / clicked.
_DISCLOSURE = re.compile(r"\b(share|shared|sharing|enter|entered|click|clicked|provide|provided|disclose|disclosed|gave|give|install|installed)\b", re.I)
_DATE = re.compile(
    r"\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2}(st|nd|rd|th)? (of )?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?( \d{4})?"
    r"|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(st|nd|rd|th)?(,? \d{4})?"
    r"|(monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", re.I)
_TIME = re.compile(r"\b\d{1,2}([:.]\d{2})? ?(am|pm|a\.m\.|p\.m\.|hrs|hours)\b", re.I)


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _user_mentions(user_text: str, verb_match: str, negated: bool) -> bool:
    """True if the user said something with the same verb stem and the same polarity."""
    stem = verb_match.lower()[:4]
    for sent in re.split(r"(?<=[.!?\n])\s*", user_text):
        if stem in sent.lower() and bool(_NEG.search(sent)) == negated:
            return True
    return False


def validate_narrative(narrative: str, incident: IncidentData) -> tuple[str, list[str]]:
    """Return (validated narrative, notes describing what was removed/replaced)."""
    user_text = incident.description or ""
    known_when = f"{incident.date_time or ''} {user_text}".lower()
    actions = " ".join(incident.actions_taken).lower()
    notes: list[str] = []
    kept: list[str] = []

    for sent in _sentences(narrative):
        negated = bool(_NEG.search(sent))

        if _ACTION_CLAIM.search(sent):
            words = {w for w in re.findall(r"[a-z]{5,}", sent.lower())}
            supported = not negated and actions and any(w in actions for w in words)
            if not supported:
                notes.append(f"Removed unsupported claim about actions taken: {sent!r}")
                continue

        if _LOSS_NEG.search(sent) and incident.financial_loss is not False:
            notes.append(f"Removed unsupported claim that no money was lost: {sent!r}")
            continue
        if (_LOSS_POS.search(sent) and not negated and incident.financial_loss is not True
                and incident.amount is None and not re.search(r"\[[A-Z]", sent)):
            notes.append(f"Removed unsupported claim of financial loss: {sent!r}")
            continue

        m = _DISCLOSURE.search(sent)
        if m and re.search(r"\b(i|we|me|my)\b", sent, re.I) and not _user_mentions(user_text, m.group(0), negated):
            notes.append(f"Removed claim about what the complainant did that the user did not state: {sent!r}")
            continue

        def amount_ok(a: re.Match[str]) -> str:
            value = extract_identifiers(a.group(0)).amount
            if value is None or (incident.amount is not None and abs(value - incident.amount) < 0.5):
                return a.group(0)
            notes.append(f"Replaced unsupported amount {a.group(0)!r}")
            return "[AMOUNT]"

        sent = AMOUNT_RE.sub(amount_ok, sent)

        def date_ok(d: re.Match[str]) -> str:
            if d.group(0).lower() in known_when:
                return d.group(0)
            notes.append(f"Replaced unsupported date {d.group(0)!r}")
            return "[DATE]"

        def time_ok(t: re.Match[str]) -> str:
            if t.group(0).lower().replace(" ", "") in known_when.replace(" ", ""):
                return t.group(0)
            notes.append(f"Replaced unsupported time {t.group(0)!r}")
            return "[TIME]"

        sent = _TIME.sub(time_ok, _DATE.sub(date_ok, sent))
        kept.append(sent)

    text = " ".join(kept).strip() or "[DESCRIBE THE INCIDENT IN DETAIL]"
    return text, notes
