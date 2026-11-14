"""Inferensi model sentimen dalam Python murni (tanpa scikit-learn/scipy/joblib).

Meniru TfidfVectorizer(analyzer='char_wb', sublinear_tf, idf, L2) lalu LinearSVC dua kelas.
Bobot dibaca dari model_sentimen.json yang dibuat scripts/ekspor_model_sentimen.py.
Kesamaan dengan scikit-learn diuji di tests/test_sentimen_json.py.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

_SPASI = re.compile(r"\s\s+")


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


class ModelJSON:
    """Antarmuka sama dengan bagian yang dipakai layanan dari model scikit-learn: classes_, decision_function, predict."""

    def __init__(self, data: dict):
        self.classes_ = list(data["classes"])
        self._lo, self._hi = data["ngram"]
        self._sublinear = data["sublinear"]
        self._vocab = data["vocab"]
        self._coef = data["coef"]
        self._b = data["intercept"]

    @classmethod
    def dari_file(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _skor(self, teks: str) -> float:
        nilai = []
        for t, tf in Counter(_char_wb_ngrams(str(teks).lower(), self._lo, self._hi)).items():
            if t in self._vocab:
                idx, idf = self._vocab[t]
                nilai.append((idx, ((1.0 + math.log(tf)) if self._sublinear else float(tf)) * idf))
        norma = math.sqrt(sum(v * v for _, v in nilai))
        if norma == 0:
            return self._b
        return self._b + sum(self._coef[i] * v / norma for i, v in nilai)

    def decision_function(self, daftar):
        return [self._skor(t) for t in daftar]

    def predict(self, daftar):
        return [self.classes_[1] if s > 0 else self.classes_[0] for s in self.decision_function(daftar)]
