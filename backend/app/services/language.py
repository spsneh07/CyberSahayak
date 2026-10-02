"""Response-language selection (English, Hindi).

Only user-facing prose is generated in the selected language. Extraction, classification
and the complaint draft stay in English so structured fields, validation rules and
complaint placeholders keep working unchanged.
"""
from contextvars import ContextVar
from typing import Literal

Language = Literal["en", "hi"]
LANGUAGE_NAMES: dict[str, str] = {"en": "English", "hi": "Hindi"}

# Tasks whose free-text output is shown to the user and may be written in another language.
LOCALISED_TASKS = {"explanation", "guidance", "awareness", "conversation", "redflag_explain"}

_current: ContextVar[str] = ContextVar("response_language", default="en")


def set_language(code: str | None) -> None:
    _current.set(code if code in LANGUAGE_NAMES else "en")


def current_language() -> str:
    return _current.get()


def language_instruction(code: str | None = None) -> str:
    code = code or current_language()
    if code == "en":
        return ""
    name = LANGUAGE_NAMES[code]
    script = " in Devanagari script" if code == "hi" else ""
    return (
        f"\n\nOutput language: write every free-text value in {name}{script}, in simple everyday words. "
        "Keep the JSON keys, enum values (such as priority) and source ids exactly as specified in English. "
        "Copy identifiers exactly as given and never translate or transliterate them: phone numbers, URLs, "
        "email addresses, UPI IDs, transaction/reference IDs, amounts and source titles. "
        "Bracketed placeholders such as [FULL NAME] stay unchanged. All ground rules above still apply."
    )
