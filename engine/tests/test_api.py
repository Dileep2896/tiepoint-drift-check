"""API round trip through FastAPI's TestClient."""

from fastapi.testclient import TestClient

from tiepoint.api import create_app
from tiepoint.extract import RuleExtractor


def client():
    return TestClient(create_app(extractor=RuleExtractor(), static_dir=None))


def test_health_and_check():
    c = client()
    assert c.get("/api/health").json() == {"ok": True}
    body = c.get("/api/check?rev=C").json()
    assert body["summary"]["drift"] == 4
    assert c.get("/api/check?rev=B").json()["summary"]["current"] == 10


def test_bad_revision_is_422():
    assert client().get("/api/check?rev=Q").status_code == 422


def test_accept_attest_flow():
    c = client()
    assert c.post("/api/tiepoints/TP-01/accept?rev=C", json={}).json()["pressure_psig"] == 1025
    for party in ("upstream", "downstream"):
        assert c.post("/api/tiepoints/TP-01/attest?rev=C", json={"party": party}).status_code == 200
    rows = {r["id"]: r for r in c.get("/api/check?rev=C").json()["tie_points"]}
    assert rows["TP-01"]["status"] == "current"


def test_errors_map_to_http():
    c = client()
    assert c.post("/api/tiepoints/TP-04/accept?rev=C", json={}).status_code == 409
    assert c.post("/api/tiepoints/TP-99/accept?rev=C", json={}).status_code == 404
    assert c.post("/api/tiepoints/TP-01/attest?rev=C", json={"party": "owner"}).status_code == 422


def test_redraft_and_reset():
    c = client()
    assert c.post("/api/deliverables/DS-301/redraft?rev=C").json()["sized_on"] == 1025
    assert c.get("/api/check?rev=C").json()["summary"]["deliverables_stale"] == 3
    c.post("/api/reset")
    assert c.get("/api/check?rev=C").json()["summary"]["deliverables_stale"] == 4


def test_extract_sample_round_trip():
    c = client()
    text = c.get("/api/extract/sample").json()["text"]
    body = c.post("/api/extract", json={"text": text}).json()
    assert body["engine"] == "rules" and len(body["rows"]) == 9 and len(body["errors"]) == 1
    assert c.post("/api/extract", json={"text": ""}).status_code == 422


def test_story_uses_fresh_seed():
    c = client()
    c.post("/api/tiepoints/TP-01/accept?rev=C", json={})
    body = c.get("/api/story").json()
    assert body["before"]["current"] == 10
    assert body["after"]["current"] == 4 and body["after"]["attested_on_paper"] == 10
    assert [f["id"] for f in body["findings"]] == ["TP-01", "TP-03", "TP-04", "TP-05", "TP-07", "TP-10"]
