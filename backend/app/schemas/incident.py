from enum import Enum

from pydantic import BaseModel, Field, field_validator


class FactSource(str, Enum):
    user_provided = "user_provided"  # stated by the user
    inferred = "inferred"  # model inference from the user's words
    unknown = "unknown"  # not stated


class IncidentData(BaseModel):
    """Structured incident. Every field defaults to 'unknown' — never invented."""

    incident_type: str | None = None
    subtype: str | None = None
    description: str = ""
    date_time: str | None = Field(None, description="Date/time exactly as the user stated it")
    platform: str | None = None
    financial_loss: bool | None = None
    amount: float | None = Field(None, ge=0)
    currency: str | None = None
    phone_numbers: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    upi_ids: list[str] = Field(default_factory=list)
    account_identifiers: list[str] = Field(default_factory=list)
    evidence_available: list[str] = Field(default_factory=list)
    actions_taken: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0, le=1)
    field_sources: dict[str, FactSource] = Field(default_factory=dict)

    @field_validator(
        "phone_numbers", "emails", "urls", "upi_ids", "account_identifiers",
        "evidence_available", "actions_taken", "missing_information", mode="before",
    )
    @classmethod
    def _none_to_list(cls, v: object) -> object:
        return [] if v is None else v

    @field_validator("currency", mode="before")
    @classmethod
    def _upper(cls, v: object) -> object:
        return v.upper() if isinstance(v, str) else v


class AnalyzeRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=6000)


class ComplainantDetails(BaseModel):
    name: str | None = Field(None, max_length=120)
    contact: str | None = Field(None, max_length=200)
    address: str | None = Field(None, max_length=400)


class ComplaintRequest(BaseModel):
    complainant: ComplainantDetails | None = None
