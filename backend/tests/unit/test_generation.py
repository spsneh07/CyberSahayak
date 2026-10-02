import json

from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation
from app.schemas.incident import ComplainantDetails, IncidentData
from app.services.awareness.generator import AwarenessGenerator
from app.services.complaint.generator import ComplaintGenerator
from app.services.guidance.advisor import Advisor, scrub_unsupported

CLS = ClassificationResult(category="phishing", confidence=0.8, reasoning="link + OTP")
SRC = [Citation(id="S1", title="Report", organization="I4C", url="https://cybercrime.gov.in", category="reporting",
                document_type="curated_summary", score=0.5, excerpt="Call the helpline 1930 or visit cybercrime.gov.in.")]


def test_complaint_uses_placeholders_for_missing(llm):
    incident = IncidentData(description="Got a WhatsApp message with a link asking for OTP.", platform="WhatsApp")
    subject, body, placeholders = ComplaintGenerator(llm).generate(incident, CLS)
    assert "Phishing" in subject and "WhatsApp" in subject
    for ph in ("[FULL NAME]", "[DATE AND TIME]", "[TRANSACTION ID / UTR]"):
        assert ph in body and ph in placeholders
    assert "I hereby declare" in body


def test_complaint_fills_provided_facts(llm):
    incident = IncidentData(description="Lost money via UPI", financial_loss=True, amount=12000, currency="INR",
                            upi_ids=["buyer99@ybl"], date_time="yesterday", account_identifiers=["412345678901"])
    _, body, placeholders = ComplaintGenerator(llm).generate(
        incident, CLS, ComplainantDetails(name="Test User", contact="test@example.com"))
    assert "INR 12,000.00" in body and "buyer99@ybl" in body and "412345678901" in body
    assert "Test User" in body and "[FULL NAME]" not in placeholders


def test_complaint_narrative_cannot_invent_identifiers(llm):
    llm.queue["complaint"].append(json.dumps({"narrative": "The fraudster called from 9000000001.", "requested_assistance": []}))
    _, body, _ = ComplaintGenerator(llm).generate(IncidentData(description="scam call"), CLS)
    assert "9000000001" not in body and "[PHONE NUMBER]" in body


def test_guidance_scrubs_unsupported_contacts():
    text = scrub_unsupported("Call 155260 or visit www.fake-help.in or call 1930 or cybercrime.gov.in", SRC)
    assert "155260" not in text and "fake-help" not in text
    assert "1930" in text and "cybercrime.gov.in" in text


def test_evidence_checklist_marks_available(llm):
    incident = IncidentData(description="UPI fraud", financial_loss=True, upi_ids=["x1@ybl"],
                            evidence_available=["Screenshots"])
    g = Advisor(llm).guide(incident, CLS, SRC)
    items = [e.item for e in g.evidence_checklist]
    assert any("UPI ID" in i for i in items) and any("transaction" in i.lower() for i in items)
    assert any(e.already_available for e in g.evidence_checklist if "Screenshot" in e.item)
    assert g.evidence_checklist[0].priority == "high"


def test_awareness_resources_only_from_sources(llm):
    llm.queue["awareness"].append(json.dumps({
        "headline": "h", "resources": [{"title": "Fake", "url": "https://invented.example"}]}))
    a = AwarenessGenerator(llm).generate(IncidentData(description="x"), CLS, SRC)
    assert [r.url for r in a.resources] == ["https://cybercrime.gov.in"]


def test_every_bracketed_gap_is_reported_as_placeholder(llm):
    _, body, placeholders = ComplaintGenerator(llm).generate(IncidentData(description="scam"), CLS)
    import re

    assert set(re.findall(r"\[[^\]]+\]", body)) == set(placeholders)


def test_awareness_resources_deduplicated(llm):
    a = AwarenessGenerator(llm).generate(IncidentData(description="x"), CLS, SRC + [SRC[0].model_copy(update={"id": "S2"})])
    assert len({r.url for r in a.resources}) == len(a.resources)


def test_guidance_and_awareness_drop_evidence_destruction(llm):
    llm.queue["guidance"].append(json.dumps({"immediate_actions": ["Call your bank", "Delete the suspicious link from your device"],
                                             "do_not": ["Do not delete the chats"]}))
    g = Advisor(llm).guide(IncidentData(description="x"), CLS, SRC)
    assert g.immediate_actions == ["Call your bank"] and g.do_not == ["Do not delete the chats"]
    llm.queue["awareness"].append(json.dumps({"headline": "h", "prevention_tips": ["Delete the message after a screenshot", "Verify via official numbers"]}))
    a = AwarenessGenerator(llm).generate(IncidentData(description="x"), CLS, SRC)
    assert a.prevention_tips == ["Verify via official numbers"]
