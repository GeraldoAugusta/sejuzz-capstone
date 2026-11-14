from pathlib import Path

import pytest

from app.sentimen import layanan
from app.sentimen.inferensi import ModelJSON
from app.sentimen.utils_teks import bersihkan

BASE = Path(layanan.__file__).resolve().parent
JSON_ADA = (BASE / "model_sentimen.json").exists()
pytestmark = pytest.mark.skipif(not JSON_ADA, reason="model_sentimen.json belum ada (jalankan scripts/ekspor_model_sentimen.py)")

KALIMAT = [
    "Jusnya segar banget, manisnya pas", "Pelayanannya ramah dan cepat, pasti balik lagi", "Tempatnya bersih dan nyaman buat nongkrong",
    "Harga terjangkau, rasanya enak", "Mantab jusnya, recommended", "Baguss tempatnya, adem", "Tempat enak",
    "Nice place, the juice is fresh and tasty", "Antrinya agak lama tapi jusnya enak banget dan worth it",
    "Lama banget nunggu, pesanan saya juga salah", "Jusnya encer dan terlalu manis, kecewa", "Pelayanannya lambat dan kasirnya jutek",
    "Tempatnya kotor dan banyak lalat", "Cupnya bocor, jus tumpah semua", "Pelayanan buruk", "Nggak recommended, gak bakal balik lagi",
    "Very slow service and the juice was too sweet", "Rekomendasi", "Recommended", "Biasa aja sih",
    "a", "zzzz qqqq", "ÀÉÎ ünïcode kafe", "enak " * 200, "baguuuus bangeeet jusnyaaa",
]


def test_json_dua_kelas_dan_bentuk_keluaran():
    m = ModelJSON.dari_file(BASE / "model_sentimen.json")
    assert len(m.classes_) == 2
    skor = m.decision_function([bersihkan(k) for k in KALIMAT])
    assert len(skor) == len(KALIMAT) and all(isinstance(s, float) for s in skor)
    assert m.predict(["jusnya enak"])[0] in m.classes_


def test_layanan_memakai_mesin_json(monkeypatch):
    layanan.reset_cache()
    info = layanan.info_model()
    assert info["mesin"] == "json" and info["versi_cocok"] is None
    hasil = layanan.analisis_banyak(["Jusnya segar banget", "👍"])
    assert hasil[0]["sentimen"] in ("positif", "negatif") and hasil[1] is None
    layanan.reset_cache()


def test_sama_dengan_scikit_learn():
    joblib = pytest.importorskip("joblib")
    pytest.importorskip("sklearn")
    asli = BASE / "model_sentimen.joblib"
    if not asli.exists():
        pytest.skip("model_sentimen.joblib tidak ada")
    pipe = joblib.load(asli)
    m = ModelJSON.dari_file(BASE / "model_sentimen.json")
    teks = [bersihkan(k) for k in KALIMAT]
    teks = [t for t in teks if t.strip()]
    ref = pipe.decision_function(teks)
    got = m.decision_function(teks)
    assert max(abs(a - b) for a, b in zip(ref, got)) < 1e-6
    assert list(pipe.predict(teks)) == m.predict(teks)
