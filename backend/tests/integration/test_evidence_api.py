import hashlib

from tests.conftest import DEMO

SHA = hashlib.sha256(b"screenshot bytes").hexdigest()
FILE = {"name": "whatsapp_chat.png", "size": 16, "media_type": "image/png", "sha256": SHA,
        "recorded_at": "2026-10-03T10:30:00Z", "checklist_item": "Screenshots of all messages"}


def test_manifest_and_verify(client):
    m = client.post("/api/v1/evidence/manifest", json={"files": [FILE]})
    assert m.status_code == 200, m.text
    manifest = m.json()
    assert manifest["algorithm"] == "SHA-256" and len(manifest["manifest_sha256"]) == 64

    ok = client.post("/api/v1/evidence/verify", json={"manifest": manifest, "sha256": SHA}).json()
    assert ok["match"] and ok["manifest_intact"]

    other = hashlib.sha256(b"edited").hexdigest()
    bad = client.post("/api/v1/evidence/verify", json={"manifest": manifest, "sha256": other}).json()
    assert not bad["match"]

    manifest["files"][0]["size"] = 999  # tampering with the manifest is detected
    forged = client.post("/api/v1/evidence/verify", json={"manifest": manifest, "sha256": SHA}).json()
    assert not forged["manifest_intact"] and not forged["match"]


def test_manifest_rejects_bad_input(client):
    assert client.post("/api/v1/evidence/manifest", json={"files": []}).status_code == 422
    assert client.post("/api/v1/evidence/manifest", json={"files": [{**FILE, "sha256": "xyz"}]}).status_code == 422


def test_complaint_annexure_via_chat_and_incident_api(client):
    cid = client.post("/api/v1/conversations", json={}).json()["id"]
    first = client.post(f"/api/v1/conversations/{cid}/messages", json={"content": DEMO}).json()
    comp = client.post(f"/api/v1/conversations/{cid}/messages", json={
        "content": "Please draft a complaint", "action": "generate_complaint", "evidence_files": [FILE]}).json()
    body = comp["complaint"]["body"]
    assert "Annexure A" in body and SHA in body and "[FULL NAME]" in body

    direct = client.post(f"/api/v1/incidents/{first['incident_id']}/complaint", json={"evidence_files": [FILE]}).json()
    assert SHA in direct["body"]
    plain = client.post(f"/api/v1/incidents/{first['incident_id']}/complaint").json()
    assert "Annexure A" not in plain["body"]
