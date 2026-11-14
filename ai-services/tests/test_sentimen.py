"""
Tes modul sentimen lewat aplikasi utama (app.main), jadi ikut menguji pemasangan router,
API key (X-API-Key), dan format error seragam milik tim.

Jalankan dari folder ai-services:  python -m pytest tests/test_sentimen.py -v
"""
import json
import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sentimen import layanan

URL = "/api/v1/sentimen"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _bersihkan_cache(monkeypatch):
    monkeypatch.delenv("SERVICE_API_KEY", raising=False)     # bawaan: tanpa API key (seperti lokal)
    yield
    layanan.reset_cache()


def test_route_lama_tetap_jalan(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("teks,harapan", [
    ("Jusnya segar banget, pelayanannya ramah dan cepat", "positif"),
    ("Tempatnya bersih dan nyaman buat nongkrong", "positif"),
    ("Lama banget nunggu, pesanan saya juga salah", "negatif"),
    ("Pelayanannya lambat dan kasirnya jutek", "negatif"),
])
def test_sentimen_satu_kalimat(client, teks, harapan):
    r = client.post(URL, json={"teks": teks})
    assert r.status_code == 200
    body = r.json()
    assert body["sentimen"] == harapan
    assert isinstance(body["skor"], float) and isinstance(body["yakin"], bool)


def test_peringatan_bahasa_inggris(client):
    r = client.post(URL, json={"teks": "Very slow service and the juice was too sweet"})
    assert r.status_code == 200 and r.json()["peringatan"] is not None


def test_kalimat_indonesia_tanpa_peringatan(client):
    assert client.post(URL, json={"teks": "Jusnya enak banget"}).json()["peringatan"] is None


@pytest.mark.parametrize("teks", ["👍👍👍", "12345", "!!!"])
def test_kalimat_tanpa_kata_ditolak(client, teks):
    r = client.post(URL, json={"teks": teks})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "TEXT_NOT_ANALYZABLE"


@pytest.mark.parametrize("payload", [{"teks": ""}, {}, {"teks": "enak " * 300}])
def test_input_tidak_valid_memakai_format_error_tim(client, payload):
    r = client.post(URL, json=payload)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"       # dari handler global di app/main.py


def test_batch(client):
    daftar = ["Jusnya segar banget", "Pelayanannya lambat dan kasirnya jutek", "👍", "Harga terjangkau, rasanya enak"]
    r = client.post(f"{URL}/batch", json={"daftar_teks": daftar})
    assert r.status_code == 200
    b = r.json()
    assert b["jumlah"] == 4 and b["jumlah_tidak_terbaca"] == 1
    assert b["jumlah_positif"] + b["jumlah_negatif"] == 3
    assert [h["teks"] for h in b["hasil"]] == daftar              # urutan sama dengan masukan
    assert b["hasil"][2]["sentimen"] is None


@pytest.mark.parametrize("daftar", [["enak"] * 101, []])
def test_batch_tidak_valid_ditolak(client, daftar):
    r = client.post(f"{URL}/batch", json={"daftar_teks": daftar})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_info(client):
    r = client.get(f"{URL}/info")
    assert r.status_code == 200
    assert r.json()["label"] == ["negatif", "positif"]
    assert r.json()["versi_cocok"] in (True, None)       # model dilatih dengan scikit-learn yang sama dengan lingkungan tes


def test_versi_berbeda_terdeteksi(client, monkeypatch, tmp_path):
    asli = layanan.MODEL_PATH
    shutil.copy(asli, tmp_path / "model_sentimen.joblib")
    info = json.loads(asli.with_name("model_info.json").read_text(encoding="utf-8"))
    info["sklearn_version"] = "0.0.1"             # pura-pura model dilatih dengan versi lain
    (tmp_path / "model_info.json").write_text(json.dumps(info), encoding="utf-8")
    monkeypatch.setattr(layanan, "MODEL_PATH", tmp_path / "model_sentimen.joblib")
    layanan.reset_cache()
    r = client.get(f"{URL}/info")
    assert r.status_code == 200 and r.json()["versi_cocok"] is False


def test_model_hilang_memberi_503(client, monkeypatch, tmp_path):
    monkeypatch.setattr(layanan, "MODEL_PATH", tmp_path / "tidak_ada.joblib")
    layanan.reset_cache()
    for r in (client.post(URL, json={"teks": "enak banget"}),
              client.post(f"{URL}/batch", json={"daftar_teks": ["enak banget"]}),
              client.get(f"{URL}/info")):
        assert r.status_code == 503
        err = r.json()["error"]
        assert err["code"] == "MODEL_UNAVAILABLE"
        assert "latih_model_sentimen.py" in err["message"]
        assert str(tmp_path) not in err["message"]                # jalur server tidak bocor ke klien


# ---------- API key (X-API-Key), sama seperti router lain ----------
@pytest.mark.parametrize("metode,path,kirim", [
    ("post", URL, {"json": {"teks": "enak banget"}}),
    ("post", f"{URL}/batch", {"json": {"daftar_teks": ["enak banget"]}}),
    ("get", f"{URL}/info", {}),
])
def test_dilindungi_api_key(client, monkeypatch, metode, path, kirim):
    monkeypatch.setenv("SERVICE_API_KEY", "rahasia-tes")
    r = getattr(client, metode)(path, **kirim)                    # tanpa header
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"
    r = getattr(client, metode)(path, headers={"X-API-Key": "salah"}, **kirim)
    assert r.status_code == 401
    r = getattr(client, metode)(path, headers={"X-API-Key": "rahasia-tes"}, **kirim)
    assert r.status_code == 200


def test_tanpa_service_api_key_tidak_perlu_header(client):
    assert client.post(URL, json={"teks": "enak banget"}).status_code == 200
