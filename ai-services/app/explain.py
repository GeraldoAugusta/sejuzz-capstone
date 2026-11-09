"""Penjelasan hasil hitung: LLM bila bisa dan angkanya cocok, selain itu template."""
import logging
import re

from app import fallback, llm, prompts

log = logging.getLogger("sejuzz.ai")


def angka_cocok(teks: str, calc: dict) -> bool:
    """Jawaban LLM wajib memuat jumlah cup hasil rumus sebagai angka utuh (bukan bagian angka lain)."""
    return re.search(rf"(?<![\d.,]){calc['jumlah_cup']}(?![\d])", teks) is not None


def kisaran(calc: dict) -> str:
    """Kalimat kisaran dari kode (bukan LLM), supaya angkanya pasti dari data."""
    r = calc.get("rentang")
    if not r:
        return ""
    sumber = " (berdasarkan data simulasi)" if r.get("jenis_data") == "simulasi" else ""
    if r["cup_min"] == r["cup_max"]:
        return f" Kisarannya sekitar {r['cup_min']} cup{sumber}."
    return f" Kisaran wajarnya {r['cup_min']} sampai {r['cup_max']} cup{sumber}."


def explain_calc(calc: dict, amount, unit: str):
    """Kembalikan (teks, source, model). source = 'llm' atau 'fallback'."""
    try:
        teks, model = llm.generate(prompts.build_prompt(calc, amount, unit), system=prompts.SYSTEM)
        if angka_cocok(teks, calc):
            return teks + kisaran(calc), "llm", model
        log.warning("Jawaban LLM tidak memuat jumlah cup %s, pakai template", calc["jumlah_cup"])
    except llm.LLMError as e:
        log.warning("LLM gagal, pakai template: %s", e)
    return fallback.explain_template(calc, amount, unit) + kisaran(calc), "fallback", None
