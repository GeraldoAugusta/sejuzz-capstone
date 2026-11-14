"""
Logika sentimen: memuat model dan menebak sentimen ulasan. Tidak bergantung pada FastAPI.
Dipakai oleh app/routers/sentimen.py.

Pengaturan (opsional): environment variable SENTIMEN_MODEL_PATH untuk memindah lokasi model.
"""
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from .utils_teks import bersihkan

log = logging.getLogger("sentimen")
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("SENTIMEN_MODEL_PATH", BASE_DIR / "model_sentimen.joblib"))
BATAS_RAGU = 0.5   # |skor| di bawah ini ditandai "tidak yakin" (aturan kasar)

# Kata fungsi bahasa Inggris. Hanya dipakai untuk memberi PERINGATAN (bukan deteksi bahasa yang sebenarnya),
# karena model terbukti lemah pada kalimat berbahasa Inggris.
KATA_INGGRIS = {"the", "and", "was", "is", "are", "very", "but", "too", "with", "this", "that", "for", "not", "you"}
PERINGATAN_INGGRIS = ("Kalimat tampaknya berbahasa Inggris. Model dilatih terutama dari teks Indonesia, "
                      "jadi hasilnya kurang andal.")
PESAN_KOSONG = "Kalimat tidak berisi kata yang bisa dianalisis (misalnya hanya emoji, angka, atau tanda baca)."


class ModelTidakTersedia(Exception):
    """Model tidak ada atau tidak bisa dibuka."""

    def __init__(self, pesan: str):
        super().__init__(pesan)
        self.pesan = pesan


def _pakai_json() -> bool:
    return MODEL_PATH.with_suffix(".json").exists()


def versi_cocok() -> Optional[bool]:
    """True kalau versi scikit-learn di server sama dengan saat model dilatih.
    None kalau tidak bisa dicek atau tidak relevan (model JSON tidak memakai scikit-learn)."""
    if _pakai_json():
        return None
    info_file = MODEL_PATH.with_name("model_info.json")
    if not info_file.exists():
        return None
    try:
        import sklearn
    except ImportError:
        return None
    dilatih = json.loads(info_file.read_text(encoding="utf-8")).get("sklearn_version")
    return dilatih == sklearn.__version__


@lru_cache(maxsize=1)
def _muat():
    if _pakai_json():  # jalur utama: Python murni, tanpa scikit-learn
        from .inferensi import ModelJSON
        return ModelJSON.dari_file(MODEL_PATH.with_suffix(".json"))
    import joblib  # cadangan: butuh scikit-learn dengan versi yang sama
    model = joblib.load(MODEL_PATH)
    if versi_cocok() is False:
        # Model tetap dipakai, tetapi hasilnya tidak terjamin. Latih ulang dengan versi yang sama dengan server.
        log.warning("Versi scikit-learn di server BERBEDA dari saat model dilatih. Hasil tidak terjamin. "
                    "Jalankan ulang scripts/latih_model_sentimen.py dengan versi yang sama dengan server.")
    return model


def reset_cache() -> None:
    _muat.cache_clear()


def get_model():
    try:
        return _muat()
    except FileNotFoundError:
        raise ModelTidakTersedia("Model sentimen belum tersedia. Jalankan scripts/latih_model_sentimen.py terlebih dahulu.")
    except Exception as e:   # file rusak atau versi scikit-learn terlalu berbeda
        raise ModelTidakTersedia("Model sentimen gagal dimuat (file rusak atau versi scikit-learn terlalu berbeda). "
                                 "Jalankan ulang scripts/latih_model_sentimen.py dengan versi yang sama dengan server. "
                                 f"Detail: {type(e).__name__}") from e


def analisis_banyak(daftar_teks: List[str]) -> List[Optional[dict]]:
    """Mengembalikan daftar hasil (None untuk kalimat yang tidak berisi kata)."""
    model = get_model()
    bersih = [bersihkan(t) for t in daftar_teks]
    idx = [i for i, b in enumerate(bersih) if b.split()]
    hasil: List[Optional[dict]] = [None] * len(daftar_teks)
    if idx:
        teks_ok = [bersih[i] for i in idx]
        label = model.predict(teks_ok)
        skor = model.decision_function(teks_ok)
        for k, i in enumerate(idx):
            peringatan = PERINGATAN_INGGRIS if len(set(bersih[i].split()) & KATA_INGGRIS) >= 2 else None
            hasil[i] = {"teks": daftar_teks[i], "sentimen": str(label[k]), "skor": round(float(skor[k]), 3),
                        "yakin": bool(abs(skor[k]) >= BATAS_RAGU), "peringatan": peringatan}
    return hasil


def info_model() -> dict:
    model = get_model()
    data = {"label": [str(k) for k in model.classes_], "batas_ragu": BATAS_RAGU}
    info_file = MODEL_PATH.with_name("model_info.json")
    if info_file.exists():
        data.update(json.loads(info_file.read_text(encoding="utf-8")))
    data["mesin"] = "json" if _pakai_json() else "joblib"
    try:
        import sklearn
        data["versi_sklearn_server"] = sklearn.__version__
    except ImportError:
        data["versi_sklearn_server"] = None
    data["versi_cocok"] = versi_cocok()      # False = model dilatih dengan versi lain, hasil tidak terjamin
    return data
