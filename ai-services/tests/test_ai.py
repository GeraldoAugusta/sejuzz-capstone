from fastapi.testclient import TestClient

from app import llm
from app.main import app

c = TestClient(app)
BODY = {"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small"}


def test_explain_llm_sukses(monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda *a, **k: ("Dapat sekitar 25 cup small ya.", "model-x"))
    r = c.post("/api/v1/ai/explain", json=BODY)
    j = r.json()
    assert r.status_code == 200 and j["source"] == "llm" and j["model"] == "model-x"
    assert j["calculation"]["jumlah_cup"] == 25  # angka tetap dari rumus


def test_explain_llm_gagal_pakai_template(monkeypatch):
    def gagal(*a, **k):
        raise llm.LLMError("tes")
    monkeypatch.setattr(llm, "generate", gagal)
    j = c.post("/api/v1/ai/explain", json=BODY).json()
    assert j["source"] == "fallback" and j["model"] is None and "25 cup" in j["explanation"]


def test_explain_angka_llm_salah_ditolak(monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda *a, **k: ("Dapat sekitar 40 cup ya.", "model-x"))
    j = c.post("/api/v1/ai/explain", json=BODY).json()
    assert j["source"] == "fallback" and "25 cup" in j["explanation"]


def test_explain_input_salah_tidak_memanggil_llm(monkeypatch):
    def jangan(*a, **k):
        raise AssertionError("LLM tidak boleh dipanggil")
    monkeypatch.setattr(llm, "generate", jangan)
    r = c.post("/api/v1/ai/explain", json={**BODY, "fruit": "durian"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "FRUIT_NOT_FOUND"


def test_chat_dengan_takaran_dari_backend(monkeypatch):
    def gagal(*a, **k):
        raise llm.LLMError("tes")
    monkeypatch.setattr(llm, "generate", gagal)
    r = c.post("/api/v1/ai/chat", json={"message": "5 kg semangka cup large", "takaran": {"semangka": {"large": 500}}})
    assert r.status_code == 200 and r.json()["calculation"]["gram_per_cup"] == 500.0


def test_chat_takaran_tidak_valid_ditolak():
    r = c.post("/api/v1/ai/chat", json={"message": "halo", "takaran": {"semangka": {"large": -1}}})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "takaran" in r.json()["error"]["message"]


def test_chat_halo():
    r = c.post("/api/v1/ai/chat", json={"message": "halo"})
    assert r.status_code == 200 and r.json()["status"] == "answered"
