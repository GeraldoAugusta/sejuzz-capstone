from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_health():
    assert c.get("/health").json() == {"status": "ok"}


def test_calculate_ok():
    r = c.post("/api/v1/calculate", json={"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small", "gram_per_cup": 350})
    assert r.status_code == 200 and r.json()["jumlah_cup"] > 0


def test_takaran_default_dari_data():
    # takaran small = 200 g (ASUMSI, data/takaran_per_cup.csv); susut semangka 48,34%
    r = c.post("/api/v1/calculate", json={"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small"})
    assert r.status_code == 200
    body = r.json()
    assert body["gram_per_cup"] == 200.0
    assert body["jumlah_cup"] == int(body["berat_isi_gram"] // 200)  # konsisten dengan rumus, tahan perubahan dataset


def test_takaran_belum_ada_ditolak_jelas(monkeypatch):
    from app import store
    monkeypatch.setattr(store, "get_fruit", lambda name: {
        "susut_persen": 30, "berat_rata_rata_gram": 3000, "gram_per_cup": {"small": None, "large": None}})
    r = c.post("/api/v1/calculate", json={"fruit": "semangka", "amount": 10})
    assert r.status_code == 400 and r.json()["error"]["code"] == "TAKARAN_NOT_SET"


def test_fruits_18_jenis():
    assert len(c.get("/api/v1/fruits").json()["fruits"]) == 18


def test_buah_tidak_ada():
    r = c.post("/api/v1/calculate", json={"fruit": "durian", "amount": 1})
    assert r.status_code == 404 and r.json()["error"]["code"] == "FRUIT_NOT_FOUND"


def test_input_salah_format_error_seragam():
    r = c.post("/api/v1/calculate", json={"fruit": "semangka", "amount": -5})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "amount" in r.json()["error"]["message"]  # menyebut field yang salah
