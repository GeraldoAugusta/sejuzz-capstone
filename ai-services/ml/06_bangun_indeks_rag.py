import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
KB = ROOT / "ml" / "rag" / "knowledge_base.md"
OUT = ROOT / "app" / "data" / "rag_index.json"
BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY = os.getenv("LLM_API_KEY", "")


def keluar(pesan):
    print("GAGAL:", pesan)
    sys.exit(1)


def baca_kb():
    chunks, cur = [], None
    for baris in KB.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+([\w-]+)\s*\|\s*(.+)$", baris)
        if m:
            cur = {"id": m.group(1), "judul": m.group(2).strip(), "teks": ""}
            chunks.append(cur)
        elif cur is not None and baris.strip() and not baris.startswith("#"):
            cur["teks"] += (" " if cur["teks"] else "") + baris.strip()
    ids = [c["id"] for c in chunks]
    if len(ids) != len(set(ids)) or any(not c["teks"] for c in chunks):
        keluar("id ganda atau potongan kosong di knowledge_base.md")
    return chunks


def daftar_model():
    r = httpx.get(f"{BASE}/models", headers={"x-goog-api-key": KEY}, params={"pageSize": 200}, timeout=30)
    if r.status_code != 200:
        keluar(f"status {r.status_code}: {r.text[:200]}")
    print("Model embedding (mendukung embedContent):")
    for m in r.json().get("models", []):
        if {"embedContent", "batchEmbedContents"} & set(m.get("supportedGenerationMethods", [])):
            print(" -", m["name"].replace("models/", ""))


def embed(model, chunks, dim):
    permintaan = []
    for c in chunks:
        p = {"model": f"models/{model}", "content": {"parts": [{"text": c["teks"]}]},
             "taskType": "RETRIEVAL_DOCUMENT", "title": c["judul"]}
        if dim:
            p["outputDimensionality"] = dim
        permintaan.append(p)
    for percobaan in range(1, 6):
        try:
            r = httpx.post(f"{BASE}/models/{model}:batchEmbedContents", headers={"x-goog-api-key": KEY},
                           json={"requests": permintaan}, timeout=90)
        except httpx.HTTPError as e:
            print(f"  percobaan {percobaan}: {type(e).__name__}")
        else:
            if r.status_code == 200:
                return [e["values"] for e in r.json()["embeddings"]]
            if r.status_code not in (429, 500, 503):
                keluar(f"status {r.status_code}: {r.text[:300]}")
            print(f"  percobaan {percobaan}: status {r.status_code}")
        time.sleep(2 ** percobaan)
    keluar("embedding gagal setelah 5 percobaan (coba lagi nanti atau model lain)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--model", default=os.getenv("EMBED_MODEL", ""))
    ap.add_argument("--dim", type=int, default=0, help="opsional: dimensi keluaran (bila model mendukung)")
    a = ap.parse_args()
    if not KEY or KEY.startswith("isi_api_key"):
        keluar("LLM_API_KEY belum diisi di .env")
    if a.list:
        return daftar_model()
    model = a.model.replace("models/", "").strip()
    if not model:
        keluar("model embedding belum dipilih: jalankan --list lalu pakai --model NAMA")
    chunks = baca_kb()
    print(f"{len(chunks)} potongan dari {KB.name}; embedding dengan {model} ...")
    vek = embed(model, chunks, a.dim or None)
    if len(vek) != len(chunks) or len({len(v) for v in vek}) != 1:
        keluar("jumlah atau dimensi vektor tidak konsisten")
    for c, v in zip(chunks, vek):
        c["vektor"] = [round(float(x), 6) for x in v]
    data = {"model": model, "dim": len(vek[0]), "dim_diminta": a.dim or None, "dibuat": date.today().isoformat(),
            "jumlah": len(chunks), "chunks": chunks}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Tersimpan: {OUT} ({OUT.stat().st_size / 1024:.0f} KB), dimensi {data['dim']}.")
    print("Lanjut: python3 ml/07_uji_rag.py")


if __name__ == "__main__":
    main()
