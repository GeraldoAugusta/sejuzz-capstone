"""Langkah 1 model regresi: periksa dataset DS (kualitas, sebaran, outlier).

Jalankan dari folder ai-services/ (butuh: pip install -r requirements-ml.txt):
    python ml/01_eksplorasi_data.py
Keluaran: tabel di layar, ml/output/ringkasan_per_buah.csv, dan (bila matplotlib ada) ml/output/yield_per_buah.png
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "output"
OUT.mkdir(parents=True, exist_ok=True)

d = pd.read_csv(ROOT / "data" / "data_buah_clean.csv")
print(f"Baris: {len(d)} | Buah: {d.jenis_buah.nunique()} | Nilai kosong: {int(d.isna().sum().sum())}")

# 1) konsistensi data
ok_yield = ((d.berat_bagian_layak_g / d.berat_buah_utuh_g - d.yield_pct).abs() < 1e-3).mean()
ok_massa = ((d.berat_buah_utuh_g - d.berat_bagian_layak_g - d.berat_sisa_g) == d.selisih_g).mean()
print(f"yield = layak/utuh cocok: {ok_yield:.0%} | utuh = layak+sisa+selisih cocok: {ok_massa:.0%}")

# 2) ringkasan per buah
g = d.groupby("jenis_buah")
r = pd.DataFrame({
    "n": g.size(),
    "yield_mean": g.yield_pct.mean().round(3),
    "yield_std": g.yield_pct.std().round(3),
    "yield_min": g.yield_pct.min().round(3),
    "yield_max": g.yield_pct.max().round(3),
    "cv_yield_persen": (g.yield_pct.std() / g.yield_pct.mean() * 100).round(1),
    "korelasi_utuh_vs_yield": g.apply(lambda x: x.berat_buah_utuh_g.corr(x.yield_pct), include_groups=False).round(2),
    "korelasi_utuh_vs_layak": g.apply(lambda x: x.berat_buah_utuh_g.corr(x.berat_bagian_layak_g), include_groups=False).round(3),
})

# 3) outlier (IQR) per buah
def n_outlier(x):
    q1, q3 = x.yield_pct.quantile([0.25, 0.75])
    i = q3 - q1
    return int(((x.yield_pct < q1 - 1.5 * i) | (x.yield_pct > q3 + 1.5 * i)).sum())

r["outlier_iqr"] = g.apply(n_outlier, include_groups=False)
print(r.to_string())
print("Total outlier (IQR):", int(r.outlier_iqr.sum()), "dari", len(d), "baris")
r.to_csv(OUT / "ringkasan_per_buah.csv")

# 4) grafik (opsional)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    urut = r.sort_values("yield_mean").index.tolist()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot([d[d.jenis_buah == k].yield_pct for k in urut], tick_labels=urut)
    ax.set_ylabel("yield (bagian layak / berat utuh)")
    ax.set_title("Sebaran yield per jenis buah")
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    fig.savefig(OUT / "yield_per_buah.png", dpi=130)
    print("Grafik disimpan:", OUT / "yield_per_buah.png")
except ImportError:
    print("matplotlib tidak terpasang, grafik dilewati.")
