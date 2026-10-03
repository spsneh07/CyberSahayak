"""Evidence integrity kit: manifest of client-side SHA-256 fingerprints and verification.

Only file metadata is received; file contents never reach the server."""
from fastapi import APIRouter

from app.services.evidence.manifest import (
    EvidenceManifest, ManifestRequest, VerifyRequest, VerifyResult, build_manifest, verify,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/manifest", response_model=EvidenceManifest)
def create_manifest(body: ManifestRequest) -> EvidenceManifest:
    return build_manifest(body.files)


@router.post("/verify", response_model=VerifyResult)
def verify_file(body: VerifyRequest) -> VerifyResult:
    return verify(body)
