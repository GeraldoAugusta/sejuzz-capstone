"""Inferensi model intent dalam Python murni (tanpa scikit-learn).

Meniru TfidfVectorizer (kata 1-2 gram + karakter 2-5 gram 'char_wb', sublinear tf, idf, L2) lalu Logistic Regression.
Bobot dibaca dari app/data/model_intent.json (dibuat oleh ml/05_ekspor_model_intent.py).
Bila file tidak ada, predict() mengembalikan None dan service memakai jalur LLM/aturan seperti sebelumnya.
Kesamaan dengan scikit-learn diuji di tests/test_intent_model.py.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from app.intent_prep import bersihkan

_PATH = Path(__file__).parent / "data" / "model_intent.json"
_TOKEN = re.compile(r"(?u)\b\w\w+\b")
_SPASI = re.compile(r"\s\s+")

try:
    _M = json.loads(_PATH.read_text(encoding="utf-8"))
except (OSError, ValueError):
    _M = None


def tersedia() -> bool:
    return _M is not None


def _word_ngrams(tokens, lo, hi):
    out = list(tokens) if lo == 1 else []
    n_tok = len(tokens)
    for n in range(max(lo, 2), min(hi + 1, n_tok + 1)):
        for i in range(n_tok - n + 1):
            out.append(" ".join(tokens[i:i + n]))
    return out


def _char_wb_ngrams(teks, lo, hi):
    out = []
    for w in _SPASI.sub(" ", teks).split():
        w = " " + w + " "
        w_len = len(w)
        for n in range(lo, hi + 1):
            offset = 0
            out.append(w[offset:offset + n])
            while offset + n < w_len:
                offset += 1
                out.append(w[offset:offset + n])
            if offset == 0:  # kata pendek hanya dihitung sekali
                break
    return out


def _vektor(teks: str, f: dict):
    """Kembalikan daftar (indeks_global, nilai) hasil TF-IDF ter-L2 untuk satu vectorizer."""
    lo, hi = f["ngram"]
    istilah = _word_ngrams(_TOKEN.findall(teks), lo, hi) if f["analyzer"] == "word" else _char_wb_ngrams(teks, lo, hi)
    nilai = []
    for t, tf in Counter(istilah).items():
        if t in f["vocab"]:
            idx, idf = f["vocab"][t]
            nilai.append((f["offset"] + idx, ((1.0 + math.log(tf)) if f["sublinear"] else float(tf)) * idf))
    norma = math.sqrt(sum(v * v for _, v in nilai))
    return [(i, v / norma) for i, v in nilai] if norma > 0 else []


def predict(teks: str):
    """Kembalikan {"intent", "confidence", "probs"} atau None bila model tidak tersedia."""
    if _M is None:
        return None
    bersih = bersihkan(teks)
    aktif = [p for f in _M["fitur"] for p in _vektor(bersih, f)]
    logit = []
    for baris, b in zip(_M["coef"], _M["intercept"]):
        logit.append(b + sum(baris[i] * v for i, v in aktif))
    m = max(logit)
    e = [math.exp(x - m) for x in logit]
    z = sum(e)
    probs = [x / z for x in e]
    k = max(range(len(probs)), key=probs.__getitem__)
    return {"intent": _M["classes"][k], "confidence": probs[k],
            "probs": {c: round(p, 4) for c, p in zip(_M["classes"], probs)}}
