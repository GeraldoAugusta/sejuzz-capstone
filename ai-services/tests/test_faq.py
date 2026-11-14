from fastapi.testclient import TestClient

from app import rag
from app.main import app

c = TestClient(app)


def test_faq_menjawab(monkeypatch):
    monkeypatch.setattr(rag, "jawab", lambda q: {"teks": "Karena ada rentang.", "sumber": ["rentang-estimasi"], "skor": 0.7,
                                                  "mesin": "python", "model": "m", "embedding": "e"})
    r = c.post("/api/v1/ai/faq", json={"question": "kenapa ada kisaran cup?"})
    j = r.json()
    assert r.status_code == 200 and j["status"] == "answered" and j["rag"]["sumber"] == ["rentang-estimasi"]


def test_faq_tidak_ditemukan_memberi_panduan_tetap():
    r = c.post("/api/v1/ai/faq", json={"question": "siapa presiden indonesia"})
    assert r.status_code == 200 and r.json()["status"] == "not_found" and r.json()["rag"] is None


def test_faq_input_salah():
    assert c.post("/api/v1/ai/faq", json={"question": ""}).status_code == 422
