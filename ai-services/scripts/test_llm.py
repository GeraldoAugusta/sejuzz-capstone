"""Uji koneksi ke Gemini API.

Jalankan dari folder ai-services/:
    python scripts/test_llm.py --list              # daftar model untuk key Anda
    python scripts/test_llm.py                     # uji LLM_MODEL di .env
    python scripts/test_llm.py --model NAMA        # uji model tertentu
    python scripts/test_llm.py --semua             # coba beberapa model, tampilkan yang berhasil

Butuh .env berisi LLM_API_KEY. Jangan pernah commit .env.
"""
import argparse
import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY = os.getenv("LLM_API_KEY", "")
TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
ENV_MODEL = (os.getenv("LLM_MODEL") or "").split("#")[0].strip().replace("models/", "")
KANDIDAT = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite",
            "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]


def fail(msg: str) -> None:
    print("GAGAL:", msg)
    sys.exit(1)


def list_models() -> None:
    r = httpx.get(f"{BASE}/models", headers={"x-goog-api-key": KEY}, timeout=TIMEOUT, params={"pageSize": 200})
    if r.status_code != 200:
        fail(f"status {r.status_code}: {r.text[:300]}")
    print("Model yang mendukung generateContent:")
    for m in r.json().get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(" -", m["name"].replace("models/", ""))


def ping(model: str, attempts: int = 4):
    """Kembalikan (berhasil, pesan)."""
    body = {"contents": [{"parts": [{"text": "Balas hanya dengan satu kata: siap"}]}]}
    last = "belum dicoba"
    for attempt in range(1, attempts + 1):
        try:
            r = httpx.post(f"{BASE}/models/{model}:generateContent",
                           headers={"x-goog-api-key": KEY}, json=body, timeout=TIMEOUT)
        except httpx.TimeoutException:
            last = f"timeout (>{TIMEOUT:.0f} detik)"
        except httpx.HTTPError as e:
            return False, f"koneksi gagal: {type(e).__name__}. Cek internet/VPN/proxy."
        else:
            if r.status_code == 200:
                try:
                    return True, r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                except (KeyError, IndexError):
                    return False, f"format respons tak terduga: {r.text[:200]!r}"
            if r.status_code == 429:
                return False, "429: kuota habis / tidak ada kuota gratis untuk model ini"
            if r.status_code not in (500, 503):
                return False, f"status {r.status_code}: {r.text[:200]!r}"
            last = f"server sibuk ({r.status_code})"
        if attempt < attempts:
            wait = 2 ** attempt
            print(f"   {model}: {last}, percobaan {attempt}/{attempts}, ulangi {wait} detik lagi...")
            time.sleep(wait)
    return False, last


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--semua", action="store_true")
    a = ap.parse_args()
    if not KEY or KEY.startswith("isi_api_key"):
        fail("LLM_API_KEY belum diisi di .env.")
    if a.list:
        list_models()
    elif a.semua:
        daftar = ([ENV_MODEL] if ENV_MODEL else []) + [m for m in KANDIDAT if m != ENV_MODEL]
        berhasil = []
        for m in daftar:
            print(f"Mencoba {m} ...")
            ok, msg = ping(m, attempts=1)
            print(("   BERHASIL: " if ok else "   gagal: ") + msg)
            if ok:
                berhasil.append(m)
        print("\nModel yang berhasil:", berhasil or "tidak ada")
        if berhasil:
            print(f"Isi di .env:  LLM_MODEL={berhasil[0]}")
    else:
        model = (a.model or ENV_MODEL).replace("models/", "").strip()
        if not model:
            fail("LLM_MODEL kosong. Isi di .env atau pakai --model NAMA.")
        print(f"Memakai model: {model!r}")
        ok, msg = ping(model)
        print(("BERHASIL. Jawaban model: " if ok else "GAGAL: ") + msg)
        sys.exit(0 if ok else 1)
