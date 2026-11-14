import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.intent_prep import bersihkan  # noqa: E402

D = ROOT / "ml" / "intent_data"
OUT = ROOT / "ml" / "output"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 42
INTENTS = ["hitung_estimasi", "cek_takaran", "info_susut_buah", "bantuan_penggunaan", "out_of_scope"]


def fitur():
    return FeatureUnion([
        ("kata", TfidfVectorizer(preprocessor=bersihkan, analyzer="word", ngram_range=(1, 2), sublinear_tf=True)),
        ("karakter", TfidfVectorizer(preprocessor=bersihkan, analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)),
    ])


def model_lr(c):
    return Pipeline([("fitur", fitur()), ("clf", LogisticRegression(C=c, max_iter=2000, class_weight="balanced", random_state=SEED))])


def model_nb(alpha):
    return Pipeline([("fitur", fitur()), ("clf", ComplementNB(alpha=alpha))])


def skor(y, p):
    return {"akurasi": accuracy_score(y, p), "macro_F1": f1_score(y, p, average="macro", labels=INTENTS)}


def main():
    tr, va, te = (pd.read_csv(D / f) for f in ("intent_train_pool.csv", "intent_heldout_sintetis.csv", "intent_uji_manual.csv"))
    print("== Keseimbangan kelas (data latih) ==")
    hitung = tr.intent.value_counts()
    print(hitung.to_dict(), f"| rasio maks/min = {hitung.max() / hitung.min():.2f}")
    print("Penanganan: class_weight='balanced' pada model; kelas out_of_scope sengaja lebih banyak karena paling beragam.\n")

    # ---- cari hyperparameter pada VALIDASI (urut dari paling sederhana/teregulasi kuat)
    grid = {"Logistic Regression": [(c, model_lr) for c in (0.3, 1, 3, 10, 30)],
            "Complement Naive Bayes": [(a, model_nb) for a in (1.0, 0.3, 0.1, 0.03)]}
    terbaik, baris, hasil_grid = {}, [], []
    for nama, kombinasi in grid.items():
        for hp, fabrik in kombinasi:
            m = fabrik(hp).fit(tr.text, tr.intent)
            s = skor(va.intent, m.predict(va.text))
            hasil_grid.append({"model": nama, "hyperparameter": hp, "val_macro_F1": s["macro_F1"], "val_akurasi": s["akurasi"]})
            if nama not in terbaik or s["macro_F1"] > terbaik[nama][1]["macro_F1"] + 1e-9:
                terbaik[nama] = (hp, s, fabrik)
    pd.DataFrame(hasil_grid).round(4).to_csv(OUT / "intent_grid_validasi.csv", index=False)
    print("== Pengaruh tuning (macro-F1 pada VALIDASI) ==")
    print(pd.DataFrame(hasil_grid).round(4).to_string(index=False), "\n")

    # ---- model pembanding berbasis aturan (tanpa pelatihan)
    kandidat = {}
    try:
        from app import nlu
        kandidat["0. Aturan kata kunci (pembanding, tanpa pelatihan)"] = (None, lambda texts: [nlu.extract_rules(t)["intent"] for t in texts])
    except Exception as e:  # httpx belum terpasang dsb.
        print("Pembanding aturan dilewati:", type(e).__name__)
    for i, (nama, (hp, _, fabrik)) in enumerate(terbaik.items(), start=1):
        m = fabrik(hp).fit(tr.text, tr.intent)
        kandidat[f"{i}. TF-IDF + {nama} (param {hp})"] = (m, m.predict)

    # ---- cross-validation (hanya pelengkap: template berulang membuatnya sangat optimis)
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    cv = {n: f1_score(tr.intent, cross_val_predict(m, tr.text, tr.intent, cv=skf), average="macro")
          for n, (m, _) in kandidat.items() if m is not None}

    # ---- evaluasi tiga kelompok
    for n, (m, pred) in kandidat.items():
        sv, st = skor(va.intent, pred(va.text)), skor(te.intent, pred(te.text))
        row = {"model": n, "CV_macroF1": cv.get(n, np.nan), "valid_macroF1": sv["macro_F1"], "uji_akurasi": st["akurasi"], "uji_macroF1": st["macro_F1"]}
        if "kelompok" in te:
            for k in sorted(te.kelompok.unique()):
                mk = te.kelompok == k
                row[f"uji_macroF1_{k}"] = f1_score(te.intent[mk], pd.Series(pred(te.text))[mk.values], average="macro", labels=INTENTS)
        baris.append(row)
    tabel = pd.DataFrame(baris).round(3)
    tabel.to_csv(OUT / "intent_hasil_perbandingan.csv", index=False)
    print("== Perbandingan model ==\n" + tabel.to_string(index=False))

    # ---- pilih model terlatih pada VALIDASI (bukan uji), lalu laporan rinci pada UJI
    dilatih = {n: v for n, v in kandidat.items() if v[0] is not None}
    pilihan = max(dilatih, key=lambda n: (tabel.set_index("model").loc[n, "valid_macroF1"], n.startswith("1.")))
    m_pilih = dilatih[pilihan][0]
    p_te = m_pilih.predict(te.text)
    print(f"\nModel terpilih (berdasarkan macro-F1 VALIDASI): {pilihan}")
    lap = pd.DataFrame(classification_report(te.intent, p_te, labels=INTENTS, output_dict=True, zero_division=0)).T.round(3)
    lap.to_csv(OUT / "intent_laporan_per_kelas_uji.csv")
    print("\n== Laporan per kelas pada UJI AKHIR ==\n" + lap.to_string())
    cm = pd.DataFrame(confusion_matrix(te.intent, p_te, labels=INTENTS), index=[f"asli:{i}" for i in INTENTS], columns=INTENTS)
    cm.to_csv(OUT / "intent_confusion_uji.csv")
    print("\n== Confusion matrix UJI AKHIR ==\n" + cm.to_string())
    salah = te.assign(prediksi=p_te)[p_te != te.intent.values]
    salah.to_csv(OUT / "intent_salah_prediksi_uji.csv", index=False)
    print(f"\nKalimat uji salah prediksi: {len(salah)} dari {len(te)} (lihat ml/output/intent_salah_prediksi_uji.csv)")

    # ---- versi lain file uji (mis. intent_uji_manual_v1.csv = sebelum ditulis ulang): hanya dilaporkan, tidak dipakai memilih
    for f in sorted(D.glob("intent_uji_manual_v*.csv")):
        ex = pd.read_csv(f)
        sx = skor(ex.intent, m_pilih.predict(ex.text))
        print(f"\nUji tambahan {f.name} ({len(ex)} kalimat): akurasi {sx['akurasi']:.3f}, macro-F1 {sx['macro_F1']:.3f}")

    # ---- tulis tabel siap tempel README
    md = ["| Model | CV macro-F1 (latih) | Validasi macro-F1 (heldout sintetis) | Uji akurasi (manual) | Uji macro-F1 (manual) |", "|---|---|---|---|---|"]
    for _, r in tabel.iterrows():
        cvv = "-" if pd.isna(r.CV_macroF1) else f"{r.CV_macroF1:.3f}"
        md.append(f"| {r.model} | {cvv} | {r.valid_macroF1:.3f} | {r.uji_akurasi:.3f} | {r.uji_macroF1:.3f} |")
    md += ["", f"Model terpilih: **{pilihan}** (dipilih dari macro-F1 data validasi, bukan data uji).",
           f"Jumlah data uji manual: {len(te)} kalimat; satu kesalahan menggeser akurasi sekitar {100 / len(te):.1f} poin."]
    (OUT / "intent_tabel_perbandingan.md").write_text("\n".join(md), encoding="utf-8")

    # ---- model akhir untuk deploy: latih ulang pada LATIH + VALIDASI
    akhir = clone(m_pilih).fit(pd.concat([tr.text, va.text]), pd.concat([tr.intent, va.intent]))
    joblib.dump(akhir, OUT / "model_intent.joblib")
    print("\nModel akhir disimpan: ml/output/model_intent.joblib (dilatih pada latih + validasi)")
    print("Tabel README: ml/output/intent_tabel_perbandingan.md")


if __name__ == "__main__":
    main()
