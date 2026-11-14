"""Alur /ai/chat tanpa FastAPI: pahami kalimat, jawab sesuai intent, selalu pakai angka dari rumus/data."""
import os
import re

from app import explain, fallback, intent_model, nlu, rag, service, store

REFUSAL = ("Maaf, aku cuma bisa bantu soal estimasi cup jus Sejuzz: berapa cup dari sejumlah buah, "
           "takaran per cup, atau susut buah. Coba tanya, misalnya: \"5 kg semangka jadi berapa cup large?\"")
HELP = ("Cara pakai: pilih jenis buah, isi berat (kg) atau jumlah buah, pilih ukuran cup (small atau large), "
        "lalu lihat estimasi cup dan sisa buahnya. Kamu juga bisa langsung mengetik pertanyaan di sini, "
        "contohnya \"5 kg semangka jadi berapa cup large?\". Takaran per cup bisa diubah oleh owner di menu pengaturan takaran.")


GREETINGS = {"halo", "hallo", "hai", "hi", "hello", "helo", "p", "pagi", "siang", "sore", "malam", "assalamualaikum",
             "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "halo kak", "hai kak", "halo sejuzz"}
GREETING_REPLY = ("Halo! Aku Asisten Sejuzz. Aku bisa bantu hitung estimasi cup jus dari sejumlah buah, cek takaran per cup, "
                  "atau info susut buah. Coba tanya, misalnya: \"5 kg semangka jadi berapa cup large?\"")


def _is_greeting(message: str) -> bool:
    return re.sub(r"[^\w\s]", "", message.lower()).strip() in GREETINGS


def _norm_takaran(t) -> dict:
    """Takaran kiriman backend: {buah: {small: gram, large: gram}}. Entri tidak valid diabaikan."""
    out = {}
    for fruit, d in (t or {}).items():
        if isinstance(d, dict):
            ok = {k: float(v) for k, v in d.items() if k in ("small", "large") and isinstance(v, (int, float)) and v > 0}
            if ok:
                out[str(fruit).strip().lower()] = ok
    return out


def _resp(intent, status, reply, ext, ext_source, calc=None, missing=None, expl_source=None, model=None):
    return {"intent": intent, "status": status, "reply": reply, "calculation": calc,
            "missing": missing or [], "extraction": {k: ext.get(k) for k in ("fruit", "amount", "unit", "cup_size")},
            "extraction_source": ext_source, "explanation_source": expl_source, "model": model, "rag": None}


def _fruit_list() -> str:
    return ", ".join(store.list_fruits())


KOSONG = {"fruit": None, "fruit_unknown": None, "amount": None, "unit": None, "cup_size": None}


def _ambang(intent: str) -> float:
    """Penolakan langsung (out_of_scope) butuh keyakinan lebih tinggi: salah menolak lebih merugikan daripada salah meneruskan."""
    if intent == "out_of_scope":
        return float(os.getenv("INTENT_THRESHOLD_OOS", "0.7"))
    return float(os.getenv("INTENT_THRESHOLD", "0.6"))


def _arahkan(message: str):
    """Tentukan intent dan entitas. Kembalikan (ext, sumber_ekstraksi, sumber_intent, confidence)."""
    cls = intent_model.predict(message)
    if cls and cls["confidence"] >= _ambang(cls["intent"]):
        intent = cls["intent"]
        if intent in ("out_of_scope", "bantuan_penggunaan"):  # tidak butuh entitas, LLM tidak dipanggil
            return {**KOSONG, "intent": intent}, "none", "classifier", cls["confidence"]
        ext, esrc, _ = nlu.extract_entities(message, intent)
        return ext, esrc, "classifier", cls["confidence"]
    ext, src, _ = nlu.extract(message)  # classifier tidak ada / tidak yakin: jalur LLM lalu aturan
    return ext, src, src, (cls["confidence"] if cls else None)


def handle_message(message: str, takaran: dict | None = None) -> dict:
    """takaran (opsional): takaran per cup dari backend, diutamakan di atas takaran bawaan service."""
    tk = _norm_takaran(takaran)
    if _is_greeting(message):
        res = _resp("bantuan_penggunaan", "answered", GREETING_REPLY, KOSONG, "none")
        res.update({"intent_source": "rules", "intent_confidence": None})
        return res
    ext, src, isrc, conf = _arahkan(message)
    res = _jawab(ext, src, tk, message)
    res.update({"intent_source": isrc, "intent_confidence": None if conf is None else round(conf, 3)})
    return res


def _jawab(ext: dict, src: str, tk: dict, message: str) -> dict:
    intent = ext["intent"]
    n = fallback.fmt_num

    if intent == "out_of_scope":
        return _resp(intent, "refused", REFUSAL, ext, src)
    if intent == "bantuan_penggunaan":
        r = rag.jawab(message)  # RAG bila tersedia dan yakin; selain itu panduan tetap
        if r is None:
            return _resp(intent, "answered", HELP, ext, src)
        res = _resp(intent, "answered", r["teks"], ext, src, expl_source="llm", model=r["model"])
        res["rag"] = {"sumber": r["sumber"], "skor": r["skor"], "mesin": r["mesin"], "embedding": r["embedding"]}
        return res

    if ext["fruit"] is None:
        if ext["fruit_unknown"]:
            reply = f"Maaf, buah \"{ext['fruit_unknown']}\" belum ada di data kami. Buah yang tersedia: {_fruit_list()}."
        else:
            reply = f"Buahnya apa ya? Pilihan: {_fruit_list()}."
        return _resp(intent, "need_more_info", reply, ext, src, missing=["fruit"])

    fruit, raw = ext["fruit"], store.get_fruit(ext["fruit"])

    if intent == "cek_takaran":
        g = {**raw["gram_per_cup"], **tk.get(fruit, {})}
        if ext["cup_size"] and g.get(ext["cup_size"]) is not None:
            reply = f"Takaran {fruit} untuk cup {ext['cup_size']} adalah {n(g[ext['cup_size']])} gram per cup."
        elif g.get("small") is not None and g.get("large") is not None:
            reply = f"Takaran {fruit}: cup small {n(g['small'])} gram, cup large {n(g['large'])} gram."
        else:
            return _resp(intent, "answered", f"Takaran {fruit} belum diisi.", ext, src)
        return _resp(intent, "answered", reply + " Angka ini nilai awal yang bisa diubah owner.", ext, src)

    if intent == "info_susut_buah":
        reply = (f"Susut {fruit} sekitar {n(raw['susut_persen'])}% (rentang data {n(raw['susut_persen_min'])}% sampai "
                 f"{n(raw['susut_persen_max'])}%), dengan berat rata-rata satu buah sekitar {n(raw['berat_rata_rata_gram'])} gram.")
        return _resp(intent, "answered", reply, ext, src)

    # hitung_estimasi
    missing = [k for k, v in (("amount", ext["amount"]), ("unit", ext["unit"]), ("cup_size", ext["cup_size"])) if v is None]
    if missing:
        minta = []
        if "amount" in missing:
            minta.append("berapa jumlahnya (dalam kg atau buah)")
        elif "unit" in missing:
            minta.append(f"jumlah {n(ext['amount'])} itu dalam kg atau buah")
        if "cup_size" in missing:
            minta.append("ukuran cup-nya (small atau large)")
        return _resp(intent, "need_more_info", f"Untuk menghitung {fruit}, aku perlu tahu " + " dan ".join(minta) + ".",
                     ext, src, missing=missing)

    calc, err = service.run_calculation(fruit, ext["amount"], ext["unit"], ext["cup_size"],
                                       tk.get(fruit, {}).get(ext["cup_size"]))
    if err:
        return _resp(intent, "need_more_info", err["message"], ext, src, missing=[])
    text, esrc, model = explain.explain_calc(calc, ext["amount"], ext["unit"])
    return _resp(intent, "answered", text, ext, src, calc=calc, expl_source=esrc, model=model)
