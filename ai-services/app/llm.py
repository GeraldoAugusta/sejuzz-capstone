"""Klien LLM (Gemini REST) dengan timeout, retry, model cadangan, dan batas waktu total.

Aturan:
- Error sementara (timeout, 500, 503): ulangi pada model yang sama, lalu pindah ke model cadangan.
- Model ditutup/kuota habis/key salah (404, 429, 400, 403): langsung pindah model cadangan.
- Bila semua gagal atau batas waktu total terlewati: raise LLMError (pemanggil memakai balasan template).
Konfigurasi dibaca dari environment (.env): LLM_API_KEY, LLM_MODEL, LLM_FALLBACK_MODELS,
LLM_TIMEOUT_SECONDS, LLM_RETRIES, LLM_TOTAL_DEADLINE_SECONDS.
"""
import os
import time

import httpx

BASE = "https://generativelanguage.googleapis.com/v1beta"


class LLMError(Exception):
    """LLM tidak bisa dipakai saat ini (pesan untuk log, bukan untuk pengguna)."""


def _models() -> list[str]:
    primary = (os.getenv("LLM_MODEL") or "").split("#")[0].strip()
    extra = [m.strip() for m in (os.getenv("LLM_FALLBACK_MODELS") or "").split("#")[0].split(",") if m.strip()]
    out = []
    for m in ([primary] if primary else []) + extra:
        m = m.replace("models/", "")
        if m not in out:
            out.append(m)
    return out


def generate(prompt: str, system: str | None = None, temperature: float = 0.4, json_mode: bool = False) -> tuple[str, str]:
    """Kembalikan (teks, nama_model). Raise LLMError bila semua percobaan gagal."""
    key = os.getenv("LLM_API_KEY", "")
    if not key or key.startswith("isi_api_key"):
        raise LLMError("LLM_API_KEY belum diisi")
    models = _models()
    if not models:
        raise LLMError("LLM_MODEL belum diisi")

    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    retries = int(os.getenv("LLM_RETRIES", "2"))
    deadline = time.monotonic() + float(os.getenv("LLM_TOTAL_DEADLINE_SECONDS", "45"))

    body: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        # batas token longgar: model "thinking" ikut memakai jatah ini, terlalu kecil membuat jawaban kosong
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048},
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    errors: list[str] = []
    for model in models:
        for attempt in range(1, retries + 1):
            if time.monotonic() >= deadline:
                raise LLMError("batas waktu total terlewati: " + "; ".join(errors))
            try:
                r = httpx.post(f"{BASE}/models/{model}:generateContent",
                               headers={"x-goog-api-key": key}, json=body, timeout=timeout)
            except httpx.TimeoutException:
                errors.append(f"{model}: timeout")
            except httpx.HTTPError as e:
                errors.append(f"{model}: koneksi {type(e).__name__}")
                break  # masalah jaringan, ganti model tidak membantu banyak, tapi coba model berikutnya
            else:
                if r.status_code == 200:
                    try:
                        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    except (KeyError, IndexError, ValueError):
                        text = ""
                    if text:
                        return text, model
                    errors.append(f"{model}: jawaban kosong")
                    break
                if r.status_code in (500, 503):
                    errors.append(f"{model}: {r.status_code}")
                else:
                    errors.append(f"{model}: status {r.status_code}")
                    break  # 404/429/400/403: ulangi tidak berguna, pindah model
            if attempt < retries:
                time.sleep(min(2 ** attempt, 4))
    raise LLMError("semua model gagal: " + "; ".join(errors))
