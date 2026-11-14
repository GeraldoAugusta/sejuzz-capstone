"""
Fungsi pembersih teks. Dipakai di 02_preprocessing.py DAN 04_coba_prediksi.py.
PENTING: pembersihan saat melatih dan saat memprediksi harus SAMA persis,
makanya fungsinya ditaruh di satu file.
"""
import re

# Singkatan chat -> kata lengkap (boleh kamu tambah sendiri)
SLANG = {
    "yg": "yang", "gak": "tidak", "ga": "tidak", "nggak": "tidak", "ngga": "tidak",
    "tdk": "tidak", "gk": "tidak", "bgt": "banget", "bgus": "bagus", "udh": "sudah",
    "sdh": "sudah", "blm": "belum", "dgn": "dengan", "utk": "untuk", "krn": "karena",
    "jg": "juga", "aja": "saja", "tp": "tapi", "tpi": "tapi", "sm": "sama", "dr": "dari",
    "jd": "jadi", "bkn": "bukan", "emg": "memang", "trs": "terus", "lg": "lagi",
    "klo": "kalau", "kalo": "kalau", "hrg": "harga", "mantul": "mantap",
}


def bersihkan(teks) -> str:
    teks = str(teks).lower()                          # 1. huruf kecil semua
    teks = re.sub(r"http\S+|www\.\S+", " ", teks)     # 2. buang link
    teks = re.sub(r"@\w+|#\w+", " ", teks)            # 3. buang mention dan hashtag
    teks = re.sub(r"(.)\1{2,}", r"\1\1", teks)        # 4. "baguuuus" -> "baguus" (maks 2 huruf kembar)
    teks = re.sub(r"[^a-z\s]", " ", teks)             # 5. buang angka dan tanda baca
    kata = [SLANG.get(k, k) for k in teks.split()]    # 6. singkatan jadi kata lengkap
    return " ".join(kata)                             # 7. rapikan spasi
