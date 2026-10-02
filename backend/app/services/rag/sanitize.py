"""Cleaning and prompt-injection defence for knowledge text (treated as data, never instructions)."""
import re
import unicodedata

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts|messages)",
    r"disregard (all |any )?(the )?(previous|prior|above|system)",
    r"you are now\b",
    r"new instructions?:",
    r"\bsystem prompt\b",
    r"\bact as\b.*\b(assistant|ai|model)\b",
    r"</?(system|assistant|instructions?|source|sources|input)>",
    r"reveal (your|the) (prompt|instructions|api key)",
    r"<script\b",
]
_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_injections(text: str) -> tuple[str, int]:
    """Remove sentences/lines that look like instructions to an AI. Returns (text, removed_count)."""
    kept, removed = [], 0
    for line in text.split("\n"):
        if _INJECTION_RE.search(line):
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept), removed


def safe_attr(value: str) -> str:
    """Make metadata safe to place inside a quoted XML-like attribute."""
    return re.sub(r'[<>"\n]', " ", value)[:300]
