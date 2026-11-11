from pathlib import Path

import pytest

from app import intent_model

pytestmark = pytest.mark.skipif(not intent_model.tersedia(),
                                reason="app/data/model_intent.json belum ada (jalankan ml/05_ekspor_model_intent.py)")
ROOT = Path(__file__).resolve().parents[1]


def test_bentuk_keluaran(classifier_aktif):
    r = intent_model.predict("5 kilo semangka jadi berapa cup large?")
    assert set(r) == {"intent", "confidence", "probs"}
    assert 0 <= r["confidence"] <= 1 and abs(sum(r["probs"].values()) - 1) < 1e-2


@pytest.mark.parametrize("teks,intent", [
    ("5 kilo semangka jadi berapa cup large?", "hitung_estimasi"),
    ("takaran melon per cup berapa gram", "cek_takaran"),
    ("gimana cara ubah takaran", "bantuan_penggunaan"),
    ("siapa presiden indonesia sekarang", "out_of_scope"),
])
def test_contoh_jelas(classifier_aktif, teks, intent):
    assert intent_model.predict(teks)["intent"] == intent


@pytest.mark.parametrize("teks", ["", "?", "   ", "ÀÉÎ ünïcode", "semangka" * 50])
def test_masukan_aneh_tidak_error(classifier_aktif, teks):
    r = intent_model.predict(teks)
    assert r["intent"] in intent_model._M["classes"]


def test_sama_dengan_scikit_learn(classifier_aktif):
    joblib = pytest.importorskip("joblib")
    pytest.importorskip("sklearn")
    pd = pytest.importorskip("pandas")
    path = ROOT / "ml" / "output" / "model_intent.joblib"
    if not path.exists():
        pytest.skip("ml/output/model_intent.joblib tidak ada")
    pipe = joblib.load(path)
    teks = []
    for f in ("intent_train_pool.csv", "intent_heldout_sintetis.csv", "intent_uji_manual.csv"):
        teks += pd.read_csv(ROOT / "ml" / "intent_data" / f).text.tolist()
    P = pipe.predict_proba(teks)
    kelas = list(pipe.classes_)
    for t, p in zip(teks, P):
        r = intent_model.predict(t)
        assert r["intent"] == kelas[int(p.argmax())]
        assert abs(r["confidence"] - float(p.max())) < 1e-6
