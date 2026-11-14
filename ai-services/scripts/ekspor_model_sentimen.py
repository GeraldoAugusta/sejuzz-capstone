"""Ekspor model sentimen (joblib) ke JSON agar service berjalan TANPA scikit-learn, scipy, dan joblib.

Jalankan dari folder ai-services/ setelah scripts/latih_model_sentimen.py (butuh requirements-ml.txt):
    python3 scripts/ekspor_model_sentimen.py
Keluaran: app/sentimen/model_sentimen.json (ikut di-commit dan ikut ke container).
Lalu cek kesamaan hasil dengan model asli: python3 -m pytest tests/test_sentimen_json.py -q
"""
import json
from pathlib import Path

import joblib

RAIZ = Path(__file__).resolve().parents[1]
SUMBER = RAIZ / "app" / "sentimen" / "model_sentimen.joblib"
TUJUAN = RAIZ / "app" / "sentimen" / "model_sentimen.json"


def main():
    pipe = joblib.load(SUMBER)
    tf, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    p = tf.get_params()
    assert p["analyzer"] == "char_wb" and p["lowercase"] and p["norm"] == "l2" and p["use_idf"] and p["smooth_idf"], \
        "pengaturan TF-IDF tidak didukung oleh inferensi JSON"
    assert clf.coef_.shape[0] == 1 and len(clf.classes_) == 2, "hanya model linear dua kelas yang didukung"
    assert clf.coef_.shape[1] == len(tf.vocabulary_)
    data = {
        "versi": 1,
        "classes": [str(c) for c in clf.classes_],      # skor > 0 berarti classes[1]
        "ngram": list(p["ngram_range"]),
        "sublinear": bool(p["sublinear_tf"]),
        "vocab": {t: [int(i), float(tf.idf_[i])] for t, i in tf.vocabulary_.items()},
        "coef": [round(float(x), 10) for x in clf.coef_[0]],
        "intercept": round(float(clf.intercept_[0]), 10),
    }
    TUJUAN.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Tersimpan: {TUJUAN} ({TUJUAN.stat().st_size / 1024:.0f} KB), {len(data['coef'])} fitur, kelas: {data['classes']}")


if __name__ == "__main__":
    main()
