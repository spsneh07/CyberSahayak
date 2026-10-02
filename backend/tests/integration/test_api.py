import json

from tests.conftest import DEMO


def _conv(client) -> str:
    r = client.post("/api/v1/conversations", json={})
    assert r.status_code == 201
    return r.json()["id"]


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["knowledge_chunks"] > 0


def test_demo_flow_end_to_end(client):
    cid = _conv(client)
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": DEMO})
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["intent"] == "report_incident"
    assert res["classification"]["category"] == "phishing"
    assert res["incident"]["platform"] == "WhatsApp"
    assert res["sources"] and res["explanation"]["warning_signs"]
    assert res["guidance"]["immediate_actions"] and res["guidance"]["evidence_checklist"]
    assert res["follow_up_questions"]
    assert res["stages"][:5] == ["analyzing", "extracting", "classifying", "retrieving", "generating"]
    assert len(res["stages"]) == len(set(res["stages"]))  # each stage reported once
    assert res["provider"] == "mock"

    # Follow-up details merge into the same incident.
    r2 = client.post(f"/api/v1/conversations/{cid}/messages",
                     json={"content": "It happened yesterday. I did not share the OTP and lost no money."}).json()
    assert r2["intent"] == "provide_details"
    assert r2["incident_id"] == res["incident_id"]
    assert r2["incident"]["date_time"] and r2["incident"]["financial_loss"] is False

    comp = client.post(f"/api/v1/conversations/{cid}/messages",
                       json={"content": "Please draft a complaint", "action": "generate_complaint"}).json()
    assert "[FULL NAME]" in comp["complaint"]["body"]

    tips = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "give me safety tips"}).json()
    assert tips["intent"] == "safety_tips" and tips["awareness"]["prevention_tips"]

    conv = client.get(f"/api/v1/conversations/{cid}").json()
    assert len(conv["messages"]) == 8 and conv["incident_id"] == res["incident_id"]


def test_complaint_without_incident_asks_for_details(client):
    cid = _conv(client)
    r = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "x", "action": "generate_complaint"}).json()
    assert r["complaint"] is None and "describe" in r["reply"].lower()


def test_incident_endpoints(client):
    r = client.post("/api/v1/incidents/analyze", json={"description": DEMO})
    assert r.status_code == 201
    iid = r.json()["id"]
    assert client.get(f"/api/v1/incidents/{iid}").json()["classification"]["category"] == "phishing"
    assert client.post(f"/api/v1/incidents/{iid}/guidance").json()["guidance"]["evidence_checklist"]
    comp = client.post(f"/api/v1/incidents/{iid}/complaint", json={"complainant": {"name": "A Tester"}}).json()
    assert "A Tester" in comp["body"]
    aw = client.post(f"/api/v1/incidents/{iid}/awareness").json()
    assert aw["awareness"]["headline"]


def test_rag_search_endpoint(client):
    r = client.post("/api/v1/rag/search", json={"query": "UPI PIN to receive money", "top_k": 2})
    assert r.status_code == 200 and len(r.json()) <= 2 and r.json()[0]["url"]


def test_stream_emits_real_stages(client):
    cid = _conv(client)
    with client.stream("POST", f"/api/v1/conversations/{cid}/messages/stream", json={"content": DEMO}) as r:
        text = "".join(r.iter_text())
    events = [blk for blk in text.strip().split("\n\n") if blk]
    stages = [json.loads(e.split("data: ", 1)[1])["stage"] for e in events if e.startswith("event: stage")]
    assert stages[:4] == ["analyzing", "extracting", "classifying", "retrieving"]
    assert events[-1].startswith("event: result")


def test_validation_and_not_found_errors(client):
    r = client.post("/api/v1/incidents/analyze", json={"description": "short"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = client.get("/api/v1/incidents/does-not-exist")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    r = client.post("/api/v1/conversations/nope/messages", json={"content": "hi"})
    assert r.status_code == 404
    cid = _conv(client)
    assert client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "   "}).status_code == 422


def test_feedback(client):
    cid = _conv(client)
    client.post(f"/api/v1/conversations/{cid}/messages", json={"content": "hello"})
    msg_id = client.get(f"/api/v1/conversations/{cid}").json()["messages"][-1]["id"]
    assert client.post("/api/v1/feedback", json={"message_id": msg_id, "rating": 1}).status_code == 201
