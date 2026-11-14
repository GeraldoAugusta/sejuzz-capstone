import json
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(ROOT))
SUMBER = ROOT / "ml" / "output" / "model_intent.joblib"
TUJUAN = ROOT / "app" / "data" / "model_intent.json"


def main():
    pipe = joblib.load(SUMBER)
    union, clf = pipe.named_steps["fitur"], pipe.named_steps["clf"]
    fitur, offset = [], 0
    for nama, v in union.transformer_list:
        p = v.get_params()
        assert p["norm"] == "l2" and p["lowercase"] and p["use_idf"] and p["smooth_idf"], "pengaturan vectorizer tidak didukung"
        vocab = {t: [int(i), float(v.idf_[i])] for t, i in v.vocabulary_.items()}
        fitur.append({"nama": nama, "analyzer": p["analyzer"], "ngram": list(p["ngram_range"]),
                      "sublinear": bool(p["sublinear_tf"]), "offset": offset, "vocab": vocab})
        offset += len(vocab)
    assert clf.coef_.shape[1] == offset, "jumlah fitur tidak cocok dengan koefisien"
    data = {
        "versi": 1,
        "keterangan": "TF-IDF (kata 1-2 + karakter 2-5) + Logistic Regression. Dilatih dari data sintetis; lihat README.",
        "classes": [str(c) for c in clf.classes_],
        "fitur": fitur,
        "coef": [[round(float(x), 10) for x in row] for row in clf.coef_],
        "intercept": [round(float(x), 10) for x in clf.intercept_],
    }
    TUJUAN.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Tersimpan: {TUJUAN} ({TUJUAN.stat().st_size / 1024:.0f} KB), {offset} fitur, kelas: {data['classes']}")


if __name__ == "__main__":
    main()
