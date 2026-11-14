import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

SEED = 42
JENIS_DATA = "simulasi"  # ubah "nyata" bila memakai data timbang asli
TAKARAN_CUP_CONTOH = 200.0  # gram per cup small (asumsi), hanya untuk mengukur galat dalam satuan cup
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "output"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- 1) preprocessing
def bersihkan(df: pd.DataFrame):
    wajib = ["sample_id", "jenis_buah", "berat_buah_utuh_g", "berat_bagian_layak_g"]
    hilang = [c for c in wajib if c not in df.columns]
    if hilang:
        raise SystemExit(f"Kolom wajib tidak ada: {hilang}")
    log = {"baris_awal": len(df)}
    df = df[wajib].copy()
    df["jenis_buah"] = df["jenis_buah"].astype(str).str.strip().str.lower()
    df = df.dropna()
    log["setelah_buang_kosong"] = len(df)
    df = df.drop_duplicates(subset="sample_id")
    log["setelah_buang_id_ganda"] = len(df)
    df = df[(df.berat_buah_utuh_g > 0) & (df.berat_bagian_layak_g > 0) & (df.berat_bagian_layak_g <= df.berat_buah_utuh_g)]
    log["setelah_validasi_rentang"] = len(df)
    df = df.rename(columns={"jenis_buah": "fruit", "berat_buah_utuh_g": "utuh", "berat_bagian_layak_g": "layak"})
    df["yield"] = df["layak"] / df["utuh"]
    return df.reset_index(drop=True), log


# ---------------------------------------------------------------- 2) model
class BaselineYield(BaseEstimator, RegressorMixin):
    """Model 1: layak = utuh x rata-rata yield buah tersebut."""

    def fit(self, X, y):
        self.mean_ = (y / X["utuh"]).groupby(X["fruit"]).mean().to_dict()
        return self

    def predict(self, X):
        return X["utuh"].to_numpy() * X["fruit"].map(self.mean_).to_numpy()


class GlobalYield(BaseEstimator, RegressorMixin):
    """Model 0 (hanya pembanding): layak = utuh x rata-rata yield SEMUA buah, tanpa mengenal jenis buah."""

    def fit(self, X, y):
        self.mean_ = float((y / X["utuh"]).mean())
        return self

    def predict(self, X):
        return X["utuh"].to_numpy() * self.mean_


class LinearPerBuah(BaseEstimator, RegressorMixin):
    """Model 2: regresi linear, satu koefisien (kemiringan) per buah, tanpa intersep."""

    def _design(self, X):
        d = pd.get_dummies(X["fruit"]).reindex(columns=self.cols_, fill_value=0).astype(float)
        return d.mul(X["utuh"].to_numpy(), axis=0).to_numpy()

    def fit(self, X, y):
        self.cols_ = sorted(X["fruit"].unique())
        self.lr_ = LinearRegression(fit_intercept=False).fit(self._design(X), y)
        return self

    def predict(self, X):
        return self.lr_.predict(self._design(X))


class RandomForestYield(BaseEstimator, RegressorMixin):
    """Model 3: random forest memprediksi yield dari (buah, berat utuh), lalu dikali berat utuh."""

    def __init__(self, n_estimators=100, max_depth=None, min_samples_leaf=1, random_state=SEED):
        self.n_estimators, self.max_depth = n_estimators, max_depth
        self.min_samples_leaf, self.random_state = min_samples_leaf, random_state

    def _feat(self, X):
        d = pd.get_dummies(X["fruit"]).reindex(columns=self.cols_, fill_value=0).astype(float)
        d["utuh"] = X["utuh"].to_numpy()
        return d.to_numpy()

    def fit(self, X, y):
        self.cols_ = sorted(X["fruit"].unique())
        self.rf_ = RandomForestRegressor(
            n_estimators=self.n_estimators, max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf, random_state=self.random_state, n_jobs=-1,
        ).fit(self._feat(X), y / X["utuh"])
        return self

    def predict(self, X):
        return self.rf_.predict(self._feat(X)) * X["utuh"].to_numpy()


def metrik(y, p):
    cup = lambda g: np.floor(np.asarray(g) / TAKARAN_CUP_CONTOH)
    return {
        "MAE_gram": mean_absolute_error(y, p),
        "RMSE_gram": mean_squared_error(y, p) ** 0.5,
        "R2": r2_score(y, p),
        "MAPE_persen": float(np.mean(np.abs((y - p) / y)) * 100),
        "MAE_cup": mean_absolute_error(cup(y), cup(p)),
    }


def cv_mae(model, X, y, folds):
    hasil = []
    for tr, va in folds:
        m = model.__class__(**model.get_params()) if hasattr(model, "get_params") else model
        m.fit(X.iloc[tr], y.iloc[tr])
        hasil.append(mean_absolute_error(y.iloc[va], m.predict(X.iloc[va])))
    return float(np.mean(hasil)), float(np.std(hasil))


def main():
    df, log = bersihkan(pd.read_csv(ROOT / "data" / "data_buah_clean.csv"))
    print("Preprocessing:", log)

    # 2) keseimbangan kelas
    hitung = df["fruit"].value_counts()
    print(f"Sampel per buah: min {hitung.min()}, maks {hitung.max()} -> "
          f"{'seimbang, tidak perlu penanganan' if hitung.max() / hitung.min() <= 1.5 else 'TIDAK seimbang, perlu ditangani'}")

    # 3) pembagian data latih/uji (stratified per buah), data uji disimpan dan tidak disentuh sampai akhir
    X, y = df[["fruit", "utuh"]], df["layak"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=df["fruit"])
    Xtr, Xte, ytr, yte = Xtr.reset_index(drop=True), Xte.reset_index(drop=True), ytr.reset_index(drop=True), yte.reset_index(drop=True)
    print(f"Latih: {len(Xtr)} baris | Uji: {len(Xte)} baris")
    folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(Xtr, Xtr["fruit"]))

    # 4) tuning random forest dengan cross-validation pada data latih saja
    grid = {"n_estimators": [100, 300], "max_depth": [None, 4, 8], "min_samples_leaf": [1, 5, 15]}
    gs = GridSearchCV(RandomForestYield(), grid, cv=folds, scoring="neg_mean_absolute_error", n_jobs=1).fit(Xtr, ytr)
    rf_tuned = RandomForestYield(**gs.best_params_)
    print("Hyperparameter RF terbaik:", gs.best_params_)

    kandidat = {
        "0. Referensi (rata-rata yield semua buah)": GlobalYield(),
        "1. Baseline (rata-rata yield per buah)": BaselineYield(),
        "2. Regresi linear per buah": LinearPerBuah(),
        "3a. Random forest (bawaan)": RandomForestYield(),
        "3b. Random forest (tuning)": rf_tuned,
    }

    # 5) evaluasi: CV pada data latih (untuk memilih), lalu data uji (dilaporkan sekali)
    baris = []
    for nama, m in kandidat.items():
        cv_m, cv_s = cv_mae(m, Xtr, ytr, folds)
        m.fit(Xtr, ytr)
        baris.append({"model": nama, "CV_MAE_gram": cv_m, "CV_std": cv_s, **{f"uji_{k}": v for k, v in metrik(yte, m.predict(Xte)).items()}})
    tabel = pd.DataFrame(baris).round(3)
    tabel.to_csv(OUT / "hasil_perbandingan.csv", index=False)
    print("\n" + tabel.to_string(index=False))

    # 6) aturan pemilihan (baris 0 hanya pembanding, tidak ikut dipilih).
    #    Model rumit harus mengalahkan baseline minimal 5% pada CV, jika tidak dipakai yang paling sederhana.
    calon = tabel.iloc[1:]
    base_nama, base = calon.iloc[0]["model"], calon.iloc[0]["CV_MAE_gram"]
    terbaik = calon.loc[calon["CV_MAE_gram"].idxmin()]
    if terbaik["model"] == base_nama:
        pilihan = base_nama
        alasan = "baseline punya galat CV paling kecil, model yang lebih rumit tidak memberi perbaikan"
    elif terbaik["CV_MAE_gram"] > base * 0.95:
        pilihan = base_nama
        alasan = (f"model lain tidak mengalahkan baseline minimal 5% pada CV (terbaik {terbaik['model']}: "
                  f"{terbaik['CV_MAE_gram']:.2f} vs baseline {base:.2f} gram), jadi dipilih yang paling sederhana dan ringan di-deploy")
    else:
        pilihan, alasan = terbaik["model"], "galat CV paling kecil dan mengalahkan baseline lebih dari 5%"
    print(f"\nModel terpilih: {pilihan}\nAlasan: {alasan}")

    # 7) rentang estimasi: persentil 10-90 yield per buah dari data latih, cakupan diuji pada data uji
    q = Xtr.assign(y=ytr / Xtr["utuh"]).groupby("fruit")["y"].quantile([0.1, 0.9]).unstack()
    lo, hi = Xte["fruit"].map(q[0.1]), Xte["fruit"].map(q[0.9])
    yy = yte / Xte["utuh"]
    cakupan = float(((yy >= lo) & (yy <= hi)).mean())
    print(f"Cakupan rentang P10-P90 pada data uji: {cakupan:.1%} (target sekitar 80%)")

    # 8) artefak akhir dilatih ulang pada SEMUA data (setelah evaluasi selesai)
    semua = df.groupby("fruit")["yield"]
    artefak = {
        "_catatan": "Dihitung dari data SIMULASI tim DS. Ganti dengan data timbang nyata lalu jalankan ulang skrip.",
        "jenis_data": JENIS_DATA, "model_terpilih": pilihan, "alasan": alasan, "cakupan_p10_p90_uji": round(cakupan, 3),
        "yield_per_buah": {k: {"mean": round(float(semua.mean()[k]), 4), "p10": round(float(semua.quantile(0.1)[k]), 4),
                               "p90": round(float(semua.quantile(0.9)[k]), 4), "n": int(semua.size()[k])} for k in semua.mean().index},
    }
    teks = json.dumps(artefak, indent=2, ensure_ascii=False)
    (OUT / "yield_per_buah.json").write_text(teks, encoding="utf-8")
    (ROOT / "app" / "data" / "yield_per_buah.json").write_text(teks, encoding="utf-8")  # dibaca service untuk rentang estimasi

    # 9) tabel siap tempel ke README
    md = ["| Model | MAE CV (gram) | MAE uji (gram) | RMSE uji (gram) | R2 uji | MAE uji (cup) |", "|---|---|---|---|---|---|"]
    for _, r in tabel.iterrows():
        md.append(f"| {r['model']} | {r['CV_MAE_gram']:.2f} | {r['uji_MAE_gram']:.2f} | {r['uji_RMSE_gram']:.2f} | {r['uji_R2']:.4f} | {r['uji_MAE_cup']:.3f} |")
    md += ["", f"Model terpilih: **{pilihan}**. Alasan: {alasan}.", f"Cakupan rentang P10-P90 pada data uji: {cakupan:.1%}."]
    (OUT / "tabel_perbandingan.md").write_text("\n".join(md), encoding="utf-8")
    print("\nTersimpan di ml/output/: hasil_perbandingan.csv, tabel_perbandingan.md, yield_per_buah.json (salinan juga di app/data/)")


if __name__ == "__main__":
    main()
