from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_pipeline
from app.core.errors import NotFoundError
from app.models import Incident
from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Awareness, Citation, ComplaintDraftOut, Explanation, Guidance
from app.schemas.incident import AnalyzeRequest, ComplaintRequest, IncidentData
from app.services.incident.extractor import follow_up_questions
from app.services.pipeline import Pipeline

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentOut(BaseModel):
    id: str
    incident: IncidentData
    classification: ClassificationResult | None


class AnalysisOut(IncidentOut):
    explanation: Explanation
    guidance: Guidance
    sources: list[Citation]
    follow_up_questions: list[str]
    warnings: list[str]
    provider: str


class GuidanceOut(BaseModel):
    incident_id: str
    explanation: Explanation
    guidance: Guidance
    sources: list[Citation]


class AwarenessOut(BaseModel):
    incident_id: str
    awareness: Awareness
    sources: list[Citation]


def _get(p: Pipeline, incident_id: str) -> Incident:
    incident = p.incidents.get(incident_id)
    if incident is None:
        raise NotFoundError("Incident")
    return incident


@router.post("/analyze", response_model=AnalysisOut, status_code=201)
def analyze(body: AnalyzeRequest, p: Pipeline = Depends(get_pipeline)) -> AnalysisOut:
    out = p.analyze(body.description)
    return AnalysisOut(
        id=out["incident"].id, incident=out["data"], classification=out["classification"],
        explanation=out["explanation"], guidance=out["guidance"], sources=out["sources"],
        follow_up_questions=follow_up_questions(out["data"].missing_information),
        warnings=out["warnings"], provider=p.llm.name,
    )


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, p: Pipeline = Depends(get_pipeline)) -> IncidentOut:
    incident = _get(p, incident_id)
    data, cls = p.load(incident)
    return IncidentOut(id=incident.id, incident=data, classification=cls)


@router.post("/{incident_id}/guidance", response_model=GuidanceOut)
def guidance(incident_id: str, p: Pipeline = Depends(get_pipeline)) -> GuidanceOut:
    explanation, g, sources = p.guidance_for(_get(p, incident_id))
    return GuidanceOut(incident_id=incident_id, explanation=explanation, guidance=g, sources=sources)


@router.post("/{incident_id}/complaint", response_model=ComplaintDraftOut)
def complaint(incident_id: str, body: ComplaintRequest | None = None, p: Pipeline = Depends(get_pipeline)) -> ComplaintDraftOut:
    return p.complaint_for(_get(p, incident_id), body.complainant if body else None)


@router.post("/{incident_id}/awareness", response_model=AwarenessOut)
def awareness(incident_id: str, p: Pipeline = Depends(get_pipeline)) -> AwarenessOut:
    content, sources = p.awareness_for(_get(p, incident_id))
    return AwarenessOut(incident_id=incident_id, awareness=content, sources=sources)
