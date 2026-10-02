from tests.conftest import DEMO


def test_check_message_endpoint(client):
    r = client.post("/api/v1/check/message", json={"text": DEMO})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["method"] == "rule-based pattern matching"
    assert {"credential_request", "urgency_threat"} <= body["categories"].keys()
    for s in body["spans"]:
        assert DEMO[s["start"]:s["end"]] == s["text"]


def test_check_message_with_mock_llm_keeps_rule_explanations(client):
    body = client.post("/api/v1/check/message", json={"text": DEMO, "llm_explanations": True, "language": "hi"}).json()
    assert body["spans"] and all(s["explanation_source"] == "rule" for s in body["spans"])


def test_check_message_validation(client):
    assert client.post("/api/v1/check/message", json={"text": ""}).status_code == 422


def test_check_url_endpoint(client):
    bad = client.post("/api/v1/check/url", json={"url": "http://paytrn.com/kyc-update"}).json()
    assert bad["risk_level"] == "high" and bad["domain"] == "paytrn.com"
    assert any(i["code"] == "character_substitution" for i in bad["indicators"])
    good = client.post("/api/v1/check/url", json={"url": "https://www.paytm.com"}).json()
    assert good["risk_level"] == "low"


def test_conversation_check_message_includes_red_flags(client):
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": DEMO}).json()
    assert r["red_flags"]["spans"] and r["language"] == "en"
    assert r["classification"]["category"] == "phishing"  # existing flow unchanged


def test_meta_lists_languages(client):
    langs = {l["id"] for l in client.get("/api/v1/meta").json()["languages"]}
    assert langs == {"en", "hi"}
