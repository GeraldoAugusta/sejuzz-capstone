"""Bangun app/data/fruits.json dari data/data_buah_clean.csv (data timbang tim DS).

Jalankan dari folder service/:  python scripts/build_fruit_table.py
Kolom gram_per_cup TIDAK ada di dataset timbang. Takaran dibaca dari data/takaran_per_cup.csv
(kolom: jenis_buah,small_g,large_g) bila file itu ada; jika tidak, diisi null (belum ada data).
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "data_buah_clean.csv"
OUT = ROOT / "app" / "data" / "fruits.json"

df = pd.read_csv(CSV)
takaran = {}
TAKARAN_CSV = ROOT / "data" / "takaran_per_cup.csv"
if TAKARAN_CSV.exists():
    for _, r in pd.read_csv(TAKARAN_CSV).iterrows():
        takaran[r["jenis_buah"].strip().lower()] = {"small": float(r["small_g"]), "large": float(r["large_g"])}

fruits = {}
for name, g in df.groupby("jenis_buah"):
    key = name.strip().lower()
    gpc = takaran.get(key, {"small": None, "large": None})
    fruits[key] = {
        "susut_persen": round(float((1 - g["yield_pct"].mean()) * 100), 2),
        "susut_persen_min": round(float((1 - g["yield_pct"].max()) * 100), 2),
        "susut_persen_max": round(float((1 - g["yield_pct"].min()) * 100), 2),
        "berat_rata_rata_gram": round(float(g["berat_buah_utuh_g"].mean()), 1),
        "jumlah_sampel": int(len(g)),
        "gram_per_cup": gpc,
    }

OUT.write_text(json.dumps({
    "_catatan": "Dihasilkan dari data/data_buah_clean.csv oleh scripts/build_fruit_table.py. "
                "susut_persen = (1 - rata-rata yield) x 100. gram_per_cup null = belum ada data komposisi menu.",
    "fruits": dict(sorted(fruits.items())),
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(fruits)} buah ditulis ke {OUT}")
