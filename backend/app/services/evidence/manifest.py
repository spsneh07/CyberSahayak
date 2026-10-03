"""Evidence integrity manifest.

Files are fingerprinted (SHA-256) in the user's browser; only metadata reaches the server,
never file contents. The manifest is deterministic (no AI). A matching fingerprint shows a
file is byte-for-byte unchanged since it was recorded; it does not show the content is genuine.
"""
import hashlib
import json
import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

ALGORITHM = "SHA-256"
NOTE = ("Fingerprints were computed on the user's device; the files were not uploaded. A matching fingerprint "
        "shows a file has not changed since it was recorded. It does not prove the content is genuine.")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class EvidenceFile(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    size: int = Field(..., ge=0)
    media_type: str = Field("", max_length=100)
    sha256: str = Field(..., pattern=r"^[0-9a-fA-F]{64}$")
    recorded_at: datetime
    last_modified: datetime | None = Field(None, description="File timestamp reported by the device, if any")
    checklist_item: str | None = Field(None, max_length=300)

    @field_validator("name", "media_type", "checklist_item")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # no control characters; square brackets would be read as complaint placeholders
        v = _CONTROL.sub("", v).replace("[", "(").replace("]", ")").strip()
        return v

    @field_validator("sha256")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class EvidenceManifest(BaseModel):
    algorithm: str = ALGORITHM
    files: list[EvidenceFile] = Field(..., min_length=1, max_length=100)
    generated_at: datetime
    manifest_sha256: str
    note: str = NOTE


class ManifestRequest(BaseModel):
    files: list[EvidenceFile] = Field(..., min_length=1, max_length=100)


class VerifyRequest(BaseModel):
    manifest: EvidenceManifest
    sha256: str = Field(..., pattern=r"^[0-9a-fA-F]{64}$")
    name: str | None = Field(None, max_length=255)


class VerifyResult(BaseModel):
    manifest_intact: bool
    match: bool
    matched_file: EvidenceFile | None = None
    message: str


def _canonical(files: list[EvidenceFile], generated_at: datetime) -> bytes:
    payload = {"algorithm": ALGORITHM, "generated_at": generated_at.isoformat(),
               "files": [f.model_dump(mode="json") for f in files]}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def manifest_digest(files: list[EvidenceFile], generated_at: datetime) -> str:
    return hashlib.sha256(_canonical(files, generated_at)).hexdigest()


def build_manifest(files: list[EvidenceFile], now: datetime | None = None) -> EvidenceManifest:
    generated_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    return EvidenceManifest(files=files, generated_at=generated_at, manifest_sha256=manifest_digest(files, generated_at))


def verify(req: VerifyRequest) -> VerifyResult:
    m = req.manifest
    intact = manifest_digest(m.files, m.generated_at) == m.manifest_sha256.lower()
    target = req.sha256.lower()
    hit = next((f for f in m.files if f.sha256 == target), None)
    if not intact:
        msg = "The manifest itself has been changed since it was created, so it can't be relied on for verification."
    elif hit:
        msg = f"Match: this file is byte-for-byte identical to '{hit.name}' as recorded."
        if req.name and req.name != hit.name:
            msg += f" (It now has a different name: '{req.name}'.)"
    else:
        same_name = next((f for f in m.files if req.name and f.name == req.name), None)
        msg = ("No match: a file with this name was recorded, but its contents are different now. Use the original."
               if same_name else "No match: this file is not in the manifest.")
    return VerifyResult(manifest_intact=intact, match=bool(hit) and intact, matched_file=hit if intact else None, message=msg)


def annexure(files: list[EvidenceFile]) -> str:
    """Deterministic complaint annexure listing each file and its fingerprint."""
    lines = ["Annexure A: List of digital evidence files",
             f"(Fingerprint algorithm: {ALGORITHM}. Fingerprints were computed on my device when each file was recorded "
             "and can be used to check that a file has not changed since.)", ""]
    for i, f in enumerate(files, 1):
        lines.append(f"  {i}. {f.name} ({f.media_type or 'unknown type'}, {f.size:,} bytes)")
        if f.checklist_item:
            lines.append(f"     Evidence of: {f.checklist_item}")
        lines.append(f"     Recorded: {f.recorded_at.strftime('%d %B %Y %H:%M %Z').strip()}")
        lines.append(f"     SHA-256: {f.sha256}")
    return "\n".join(lines)
