"""Standalone checks: red-flag highlighting for a pasted message, and offline URL analysis."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.ai.base import LLMProvider
from app.services.ai.factory import get_llm
from app.services.language import Language, set_language
from app.services.scamcheck.red_flags import RedFlagReport, detect_red_flags, llm_explain
from app.services.scamcheck.url_analyzer import UrlAnalysis, analyze_url

router = APIRouter(prefix="/check", tags=["check"])


class MessageCheckIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=6000)
    llm_explanations: bool = Field(False, description="Let the LLM reword explanations of rule-found spans")
    language: Language = "en"


class UrlCheckIn(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


@router.post("/message", response_model=RedFlagReport)
def check_message(body: MessageCheckIn, llm: LLMProvider = Depends(get_llm)) -> RedFlagReport:
    report = detect_red_flags(body.text)
    if body.llm_explanations:
        set_language(body.language)
        report = llm_explain(report, llm)
    return report


@router.post("/url", response_model=UrlAnalysis)
def check_url(body: UrlCheckIn) -> UrlAnalysis:
    return analyze_url(body.url)
