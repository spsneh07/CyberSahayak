import json

from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation
from app.schemas.incident import IncidentData
from app.services.ai.providers.mock import MockLLM
from app.services.guidance.advisor import Advisor
from app.services.guidance.safety import destroys_evidence, scrub_reply
from app.services.language import language_instruction, set_language


class SpyLLM(MockLLM):
    """Mock LLM that records the system prompt per task and can return canned JSON."""

    def __init__(self, canned: dict | None = None):
        super().__init__()
        self.systems: dict[str, str] = {}
        self.canned = canned or {}

    def complete(self, *, task, system, user, json_schema=None):
        self.systems[task] = system
        if task in self.canned:
            return json.dumps(self.canned[task])
        return super().complete(task=task, system=system, user=user, json_schema=json_schema)


def test_english_adds_no_instruction():
    assert language_instruction("en") == ""


def test_hindi_instruction_preserves_identifiers():
    text = language_instruction("hi")
    assert "Hindi" in text and "Devanagari" in text
    for keep in ("phone numbers", "URLs", "email addresses", "UPI IDs", "transaction", "[FULL NAME]", "source ids"):
        assert keep in text


def test_only_user_facing_tasks_are_localised(client):
    llm = SpyLLM()
    from app.main import app
    from app.services.ai.factory import get_llm

    app.dependency_overrides[get_llm] = lambda: llm
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={
        "content": "I got a WhatsApp from +91 98765 43210 with link http://sbi-kyc-update.xyz asking my OTP",
        "language": "hi"}).json()
    assert r["language"] == "hi"
    for task in ("explanation", "guidance", "conversation"):
        assert "Output language" in llm.systems[task], task
    for task in ("intent", "extraction", "classification"):
        assert "Output language" not in llm.systems[task], task
    # structured fields and identifiers are unchanged by language selection
    assert "http://sbi-kyc-update.xyz" in r["incident"]["urls"]
    assert r["incident"]["phone_numbers"]
    comp = client.post(f"/api/v1/conversations/{cid}/messages", json={
        "content": "draft complaint", "action": "generate_complaint", "language": "hi"}).json()
    assert "Output language" not in llm.systems["complaint"]
    assert "[FULL NAME]" in comp["complaint"]["body"]


def test_english_request_after_hindi_is_not_localised(client):
    llm = SpyLLM()
    from app.main import app
    from app.services.ai.factory import get_llm

    app.dependency_overrides[get_llm] = lambda: llm
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "hello", "language": "hi"})
    client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "hello"})
    assert "Output language" not in llm.systems["conversation"]


def test_unsupported_language_rejected(client):
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "hi", "language": "ta"})
    assert r.status_code == 422


def test_hindi_output_still_guarded():
    """Guards still run on Hindi model output: invented URLs/helplines scrubbed, evidence deletion dropped."""
    set_language("hi")
    try:
        llm = SpyLLM({"guidance": {
            "immediate_actions": ["बैंक को तुरंत कॉल करें।", "सारी चैट डिलीट कर दें।", "https://fake-help.example पर जाएं।"],
            "security_steps": [], "reporting_guidance": ["155260 पर कॉल करें।"],
            "evidence_checklist": [], "do_not": ["चैट डिलीट न करें।"], "source_ids": ["bogus"]}})
        src = [Citation(id="d1", title="t", organization="o", url="https://cybercrime.gov.in", category="phishing",
                        document_type="curated_summary", score=0.9, excerpt="Report at cybercrime.gov.in or call 1930.")]
        g = Advisor(llm).guide(IncidentData(description="x"), ClassificationResult(category="phishing", confidence=0.9, reasoning="r"), src)
    finally:
        set_language("en")
    assert "Output language" in llm.systems["guidance"]
    assert not any("डिलीट कर" in a for a in g.immediate_actions)
    assert not any("fake-help.example" in a for a in g.immediate_actions)
    assert "155260" not in g.reporting_guidance[0]
    assert g.do_not == ["चैट डिलीट न करें।"] and g.source_ids == []


def test_hindi_evidence_guard():
    assert destroys_evidence("सारे मैसेज मिटा दें।")
    assert not destroys_evidence("मैसेज मत मिटाएं।")
    assert not destroys_evidence("अपना पासवर्ड रीसेट करें।")
    assert scrub_reply("बैंक को कॉल करें। चैट डिलीट करें। सबूत रखें।") == "बैंक को कॉल करें। सबूत रखें।"


def test_fallback_reply_follows_language(client):
    llm = SpyLLM()
    llm.queue["conversation"].extend(["not json", "still not json"])
    from app.main import app
    from app.services.ai.factory import get_llm

    app.dependency_overrides[get_llm] = lambda: llm
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "hello", "language": "hi"}).json()
    assert r["reply"].startswith("माफ़ कीजिए")
