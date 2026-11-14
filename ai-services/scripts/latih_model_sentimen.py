"""
Latih ulang model sentimen. Jalankan dari folder ai-services (akar repo):

    python scripts/latih_model_sentimen.py
    python scripts/latih_model_sentimen.py jalur/ke/data_lain.csv     # data lain (kolom: text, label)

Hasil ditulis ke app/sentimen/model_sentimen.joblib dan model_info.json.

KAPAN PERLU DIJALANKAN?
- TIDAK perlu sebelum push pertama: model yang ikut dalam paket sudah jadi.
- PERLU kalau /api/v1/sentimen/info menunjukkan versi_cocok = false (scikit-learn di server berbeda dari saat
  model dilatih), atau kalau data ulasan bertambah. Model dalam paket dilatih dengan scikit-learn 1.5.2. Jalankan dengan Python dan scikit-learn yang SAMA dengan server.

Butuh: pip install -r requirements-ml.txt (sudah memuat pandas, numpy, scikit-learn, joblib)
Butuh internet untuk mengunduh dataset publik SmSA. Kalau offline, taruh ulasan_publik.csv di data/sentimen/.
Data Sejuzz (CSV) ditaruh di data/sentimen/ dan JANGAN di-push ke GitHub (berisi ulasan asli pelanggan).
"""
import datetime
import importlib.util
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RAIZ = Path(__file__).resolve().parents[1]                 # folder ai-services
FOLDER_MODEL = RAIZ / "app" / "sentimen"
FOLDER_DATA = RAIZ / "data" / "sentimen"

# Memuat pembersih teks langsung dari berkasnya, supaya tidak ikut menjalankan app/__init__.py milik tim.
_spec = importlib.util.spec_from_file_location("utils_teks", FOLDER_MODEL / "utils_teks.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
bersihkan = _mod.bersihkan

DATA_SEJUZZ = Path(sys.argv[1]) if len(sys.argv) > 1 else FOLDER_DATA / "data_sentimen_sejuzz.csv"
BOBOT_SEJUZZ = 10   # satu ulasan Sejuzz dihitung 10x lebih penting dari satu ulasan publik
URL_SMSA = ("https://raw.githubusercontent.com/IndoNLP/indonlu/master/"
            "dataset/smsa_doc-sentiment-prosa/")


def muat_sejuzz(path):
    if not Path(path).exists():
        sys.exit(f"File data Sejuzz tidak ditemukan: {path}\n"
                 "Taruh data_sentimen_sejuzz.csv di data/sentimen/ (hanya di komputer, jangan di-push).")
    df = pd.read_csv(path)
    df["tb"] = df["text"].apply(bersihkan)
    df = df[df["tb"].str.split().str.len() >= 1]
    n_label = df.groupby("tb")["label"].nunique()
    df = df[~df["tb"].isin(n_label[n_label > 1].index)]          # buang teks sama tapi label bertentangan
    return df.drop_duplicates("tb").reset_index(drop=True)


def muat_publik():
    try:
        bagian = [pd.read_csv(f"{URL_SMSA}{n}_preprocess.tsv", sep="\t", header=None, names=["text", "label"])
                  for n in ["train", "valid", "test"]]
        df = pd.concat(bagian, ignore_index=True)
        df = df[df["label"].isin(["positive", "negative"])].copy()
        df["label"] = df["label"].map({"positive": "positif", "negative": "negatif"})
    except Exception as e:
        lokal = FOLDER_DATA / "ulasan_publik.csv"
        if not lokal.exists():
            sys.exit(f"Gagal mengunduh dataset publik ({type(e).__name__}). "
                     f"Periksa internet, atau taruh ulasan_publik.csv di {FOLDER_DATA}.")
        print("Unduhan gagal, memakai ulasan_publik.csv lokal.")
        df = pd.read_csv(lokal)
    df["tb"] = df["text"].apply(bersihkan)
    df = df[df["tb"].str.split().str.len() >= 3]
    return df.drop_duplicates("tb").reset_index(drop=True)


if __name__ == "__main__":
    sj = muat_sejuzz(DATA_SEJUZZ)
    pub = muat_publik()
    n_neg = int((sj["label"] == "negatif").sum())
    print(f"Sejuzz: {len(sj)} ulasan ({n_neg} negatif) | Publik: {len(pub)} ulasan")

    X = np.concatenate([pub["tb"].to_numpy(), sj["tb"].to_numpy()])
    y = np.concatenate([pub["label"].to_numpy(), sj["label"].to_numpy()])
    bobot = np.concatenate([np.ones(len(pub)), np.full(len(sj), BOBOT_SEJUZZ)])

    model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
        ("clf", LinearSVC(class_weight="balanced")),
    ])
    model.fit(X, y, clf__sample_weight=bobot)

    joblib.dump(model, FOLDER_MODEL / "model_sentimen.joblib")
    info = {
        "dibuat": datetime.datetime.now().isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "fitur": "TF-IDF character n-gram 2-5 (char_wb)",
        "model": "LinearSVC (class_weight=balanced)",
        "bobot_sejuzz": BOBOT_SEJUZZ,
        "jumlah_sejuzz": int(len(sj)),
        "jumlah_negatif_sejuzz": n_neg,
        "jumlah_publik": int(len(pub)),
        "label": [str(k) for k in model.classes_],
    }
    (FOLDER_MODEL / "model_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Tersimpan di {FOLDER_MODEL}: model_sentimen.joblib dan model_info.json")
    print(json.dumps(info, indent=2, ensure_ascii=False))
