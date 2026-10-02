"""Deterministic output guards applied after generation (the prompt alone is not enough)."""
import re

# Advice that would destroy evidence. Negated forms ("do not delete", "never wipe") are allowed.
_DESTROY = re.compile(r"\b(delete|deleting|erase|erasing|wipe|wiping|factory[- ]reset|clear (the |your )?(chat|history|messages?))\b", re.I)
_NEGATED = re.compile(r"\b(do not|don't|dont|never|avoid|without|instead of|not)\b[^.;]{0,40}$", re.I)


def destroys_evidence(text: str) -> bool:
    for m in _DESTROY.finditer(text):
        if not _NEGATED.search(text[: m.start()]):
            return True
    return False


def drop_evidence_destruction(items: list[str]) -> list[str]:
    return [i for i in items if not destroys_evidence(i)]


def scrub_reply(text: str) -> str:
    """Remove sentences/lines in free-text replies that advise destroying evidence."""
    kept = []
    for line in text.split("\n"):
        sentences = re.split(r"(?<=[.!?])\s+", line)
        kept.append(" ".join(s for s in sentences if not destroys_evidence(s)))
    return "\n".join(kept)
