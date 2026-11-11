"""Pembersihan teks untuk model intent. Dipakai skrip pelatihan (ml/) dan service, agar sama persis.

Langkah: huruf kecil, pisahkan angka dari huruf, samakan singkatan/slang, ganti nama buah menjadi 'fruittok'
dan angka menjadi 'numtok' (model belajar pola kalimat, bukan buah atau angka tertentu).
"""
import re

from app import store

SLANG = {
    "brp": "berapa", "berapakah": "berapa", "gr": "gram", "gm": "gram", "kilo": "kg", "kilogram": "kg",
    "yg": "yang", "ga": "nggak", "gak": "nggak", "ngga": "nggak", "tdk": "tidak", "dgn": "dengan", "sm": "sama",
    "persn": "persen", "prsen": "persen", "sih": "", "dong": "", "nih": "", "ya": "", "kak": "", "min": "",
    "tolong": "", "mau": "", "tanya": "",
}
NUM_WORDS = ("satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "setengah")
_FRUITS = sorted(store.list_fruits(), key=len, reverse=True)
_RE_FRUIT = re.compile(r"\b(" + "|".join(re.escape(f) for f in _FRUITS) + r")\b")
_RE_NUMWORD = re.compile(r"\b(" + "|".join(NUM_WORDS) + r")\b")


def bersihkan(teks) -> str:
    t = str(teks).lower().replace("rata2", "rata rata")
    t = re.sub(r"[^\w\s,.]", " ", t)
    t = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", t)
    t = _RE_FRUIT.sub(" fruittok ", t)
    t = re.sub(r"\b\d+(?:[.,]\d+)?\b", " numtok ", t)
    t = _RE_NUMWORD.sub(" numtok ", t)
    t = re.sub(r"[.,]", " ", t)
    return " ".join(w for w in (SLANG.get(x, x) for x in t.split()) if w)
