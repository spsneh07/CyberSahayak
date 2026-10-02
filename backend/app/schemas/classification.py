from pydantic import BaseModel, Field, field_validator

from app.services.classification.taxonomy import CATEGORY_IDS, normalize_category


class AlternativeCategory(BaseModel):
    category: str
    confidence: float = Field(..., ge=0, le=1)

    @field_validator("category", mode="before")
    @classmethod
    def _norm(cls, v: object) -> str:
        return normalize_category(str(v))


class ClassificationResult(BaseModel):
    category: str
    subtype: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str = ""
    alternatives: list[AlternativeCategory] = Field(default_factory=list)

    @field_validator("category", mode="before")
    @classmethod
    def _norm(cls, v: object) -> str:
        cat = normalize_category(str(v))
        if cat not in CATEGORY_IDS:
            raise ValueError(f"unknown category {v!r}")
        return cat
