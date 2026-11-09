from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
BODY = {"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small"}


def test_tanpa_service_api_key_terbuka(monkeypatch):
    monkeypatch.delenv("SERVICE_API_KEY", raising=False)
    assert c.post("/api/v1/calculate", json=BODY).status_code == 200


def test_dengan_service_api_key_wajib_header(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "rahasia-uji")
    r = c.post("/api/v1/calculate", json=BODY)
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"
    assert c.post("/api/v1/calculate", json=BODY, headers={"X-API-Key": "salah"}).status_code == 401
    assert c.post("/api/v1/calculate", json=BODY, headers={"X-API-Key": "rahasia-uji"}).status_code == 200
    assert c.post("/api/v1/ai/chat", json={"message": "halo"}).status_code == 401


def test_health_tetap_terbuka(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "rahasia-uji")
    assert c.get("/health").status_code == 200
