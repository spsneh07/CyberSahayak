import hashlib
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.classification import ClassificationResult
from app.schemas.incident import IncidentData
from app.services.ai.providers.mock import MockLLM
from app.services.complaint.generator import PLACEHOLDER_RE, ComplaintGenerator
from app.services.evidence.manifest import EvidenceFile, VerifyRequest, annexure, build_manifest, verify

T = datetime(2026, 10, 3, 10, 30, tzinfo=timezone.utc)


def ef(content: bytes, name: str = "chat.png", **kw) -> EvidenceFile:
    return EvidenceFile(name=name, size=len(content), media_type="image/png",
                        sha256=hashlib.sha256(content).hexdigest(), recorded_at=T, **kw)


def test_manifest_is_deterministic():
    files = [ef(b"one"), ef(b"two", "statement.pdf")]
    a, b = build_manifest(files, now=T), build_manifest(files, now=T)
    assert a.manifest_sha256 == b.manifest_sha256 and len(a.manifest_sha256) == 64
    assert "does not prove the content is genuine" in a.note


def test_verify_match_and_renamed():
    m = build_manifest([ef(b"original")], now=T)
    r = verify(VerifyRequest(manifest=m, sha256=hashlib.sha256(b"original").hexdigest(), name="renamed.png"))
    assert r.manifest_intact and r.match and r.matched_file.name == "chat.png"
    assert "renamed.png" in r.message


def test_verify_detects_changed_file():
    m = build_manifest([ef(b"original")], now=T)
    r = verify(VerifyRequest(manifest=m, sha256=hashlib.sha256(b"edited").hexdigest(), name="chat.png"))
    assert not r.match and "contents are different" in r.message


def test_verify_detects_tampered_manifest():
    m = build_manifest([ef(b"original")], now=T)
    forged = m.model_copy(deep=True)
    forged.files[0].sha256 = hashlib.sha256(b"edited").hexdigest()
    r = verify(VerifyRequest(manifest=forged, sha256=forged.files[0].sha256))
    assert not r.manifest_intact and not r.match and r.matched_file is None


def test_validation():
    with pytest.raises(ValidationError):
        EvidenceFile(name="x", size=1, sha256="nothex", recorded_at=T)
    with pytest.raises(ValidationError):
        EvidenceFile(name="x", size=-1, sha256="a" * 64, recorded_at=T)
    f = EvidenceFile(name="[FULL NAME]\x00.png", size=1, sha256="A" * 64, recorded_at=T)
    assert f.name == "(FULL NAME).png" and f.sha256 == "a" * 64


def test_annexure_in_complaint_without_new_placeholders():
    files = [ef(b"one", checklist_item="Screenshots of all messages"), ef(b"two", "[EVIL].pdf")]
    inc = IncidentData(description="I received a phishing message on WhatsApp.", platform="WhatsApp")
    cls = ClassificationResult(category="phishing", confidence=0.9, reasoning="r")
    gen = ComplaintGenerator(MockLLM())
    _, plain, ph_plain, _ = gen.generate(inc, cls)
    _, body, ph, _ = gen.generate(inc, cls, evidence_files=files)
    assert "Annexure A" not in plain
    assert "Annexure A" in body and files[0].sha256 in body and files[1].sha256 in body
    assert "2 digital file(s) with SHA-256 fingerprints" in body
    assert "Evidence of: Screenshots of all messages" in body
    # attached files fill the evidence list, so only that placeholder disappears; none are added
    assert set(ph) == set(ph_plain) - {"[LIST OF EVIDENCE, E.G. SCREENSHOTS, SMS, BANK STATEMENT]"}
    assert "[EVIL]" not in PLACEHOLDER_RE.findall(body)
    assert annexure(files).count("SHA-256:") == 2
