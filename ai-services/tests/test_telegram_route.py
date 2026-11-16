from fastapi.testclient import TestClient

from app import chat
from app.kanal import inti, telegram
from app.main import app

c = TestClient(app)
URL = "/kanal/telegram/webhook"
UPDATE = {"update_id": 501, "message": {"chat": {"id": 111, "type": "private"}, "text": "halo"}}


def siapkan(monkeypatch):
    monkeypatch.setattr(telegram, "_DEDUP", inti.AntiGanda())
    monkeypatch.setattr(telegram, "_BATAS", inti.BatasLaju(maks=5))
    monkeypatch.setattr(chat, "handle_message", lambda t, takaran=None: {"reply": "jawaban uji"})
    terkirim = []
    monkeypatch.setattr(telegram, "kirim_pesan", lambda cid, teks: terkirim.append((cid, teks)) or True)
    return terkirim


def test_tanpa_rahasia_terkonfigurasi_ditolak(monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    r = c.post(URL, json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": "apa-saja"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"


def test_rahasia_salah_atau_hilang_ditolak(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "rahasia-uji")
    assert c.post(URL, json=UPDATE).status_code == 403
    assert c.post(URL, json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": "salah"}).status_code == 403


def test_update_sah_dibalas(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "rahasia-uji")
    terkirim = siapkan(monkeypatch)
    r = c.post(URL, json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": "rahasia-uji"})
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert terkirim == [(111, "jawaban uji")]


def test_webhook_tidak_memakai_x_api_key(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "kunci-layanan")  # Telegram tidak bisa mengirim header ini
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "rahasia-uji")
    siapkan(monkeypatch)
    r = c.post(URL, json={**UPDATE, "update_id": 502}, headers={"X-Telegram-Bot-Api-Secret-Token": "rahasia-uji"})
    assert r.status_code == 200


def test_status_butuh_api_key(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "kunci-layanan")
    assert c.get("/kanal/telegram/status").status_code == 401
    r = c.get("/kanal/telegram/status", headers={"X-API-Key": "kunci-layanan"})
    assert r.status_code == 200 and set(r.json()) == {"token_terpasang", "rahasia_terpasang", "daftar_izin_aktif"}
