"""Rentang estimasi cup dari sebaran yield per buah (persentil 10 sampai 90).

Sumber: app/data/yield_per_buah.json, dihasilkan oleh ml/02_latih_bandingkan.py.
Bila file tidak ada, rentang tidak ditampilkan (service tetap jalan).
"""
import json
import math
from pathlib import Path

_PATH = Path(__file__).parent / "data" / "yield_per_buah.json"
try:
    _DATA = json.loads(_PATH.read_text(encoding="utf-8"))
except (OSError, ValueError):
    _DATA = {}


def hitung_rentang(fruit: str, total_gram: float, gram_per_cup: float):
    y = _DATA.get("yield_per_buah", {}).get(fruit.strip().lower())
    if not y or not gram_per_cup or gram_per_cup <= 0:
        return None
    isi_min, isi_max = total_gram * y["p10"], total_gram * y["p90"]
    return {
        "cup_min": math.floor(isi_min / gram_per_cup + 1e-9),
        "cup_max": math.floor(isi_max / gram_per_cup + 1e-9),
        "isi_gram_min": round(isi_min, 2),
        "isi_gram_max": round(isi_max, 2),
        "persentil": "P10-P90",
        "jenis_data": _DATA.get("jenis_data", "tidak diketahui"),
    }
