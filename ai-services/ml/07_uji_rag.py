import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
from app import rag  # noqa: E402

OUT = ROOT / "ml" / "output"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jawab", action="store_true")
    a = ap.parse_args()
    if not rag.tersedia():
        sys.exit("Indeks belum ada: jalankan ml/06_bangun_indeks_rag.py dulu")
    ev = pd.read_csv(ROOT / "ml" / "rag" / "rag_eval.csv").fillna("")
    baris = []
    for _, r in ev.iterrows():
        try:
            h = rag.cari(r.pertanyaan, k=3)
        except rag.RagError as e:
            sys.exit(f"GAGAL mencari: {e}")
        ids = [x["id"] for x in h]
        baris.append({"pertanyaan": r.pertanyaan, "jenis": r.jenis, "diharapkan": r.id_diharapkan, "top1": ids[0], "skor_top1": h[0]["skor"],
                      "hit1": ids[0] == r.id_diharapkan, "hit3": r.id_diharapkan in ids, "mesin": h[0]["mesin"]})
        time.sleep(0.15)
    d = pd.DataFrame(baris)
    dalam, luar = d[d.jenis == "dalam_topik"], d[d.jenis == "luar_topik"]
    print(f"Mesin vektor: {d.mesin.iloc[0]} | model embedding: {rag._INDEX['model']} | potongan: {len(rag._INDEX['chunks'])}")
    print(f"Dalam topik ({len(dalam)}): hit@1 = {dalam.hit1.mean():.3f}, hit@3 = {dalam.hit3.mean():.3f}")
    print(f"Skor top-1 dalam topik: min {dalam.skor_top1.min():.3f}, median {dalam.skor_top1.median():.3f}")
    print(f"Skor top-1 luar topik : maks {luar.skor_top1.max():.3f}, median {luar.skor_top1.median():.3f}")
    gagal = dalam[~dalam.hit1]
    if len(gagal):
        print("\nHit@1 meleset:")
        print(gagal[["pertanyaan", "diharapkan", "top1", "skor_top1"]].to_string(index=False))
    ambang = float(__import__("os").getenv("RAG_AMBANG", "0.6"))
    print(f"\nAmbang RAG_AMBANG = {ambang}: dalam topik lolos {int((dalam.skor_top1 >= ambang).sum())}/{len(dalam)}, "
          f"luar topik tertahan {int((luar.skor_top1 < ambang).sum())}/{len(luar)}")
    print("(Skor ini hanya panduan memilih ambang; jangan klaim sebagai hasil penyetelan yang bersih.)")
    md = ["| Metrik | Nilai |", "|---|---|", f"| Pertanyaan dalam topik | {len(dalam)} |", f"| Hit@1 | {dalam.hit1.mean():.3f} |",
          f"| Hit@3 | {dalam.hit3.mean():.3f} |", f"| Skor top-1 dalam topik (min / median) | {dalam.skor_top1.min():.3f} / {dalam.skor_top1.median():.3f} |",
          f"| Skor top-1 luar topik (maks / median) | {luar.skor_top1.max():.3f} / {luar.skor_top1.median():.3f} |",
          f"| Mesin vektor | {d.mesin.iloc[0]} |", f"| Model embedding | {rag._INDEX['model']} |"]
    (OUT / "rag_eval.md").write_text("\n".join(md), encoding="utf-8")
    d.to_csv(OUT / "rag_eval_detail.csv", index=False)
    if a.jawab:
        print("\n== Jawaban lengkap (contoh) ==")
        for q in list(dalam.pertanyaan.head(4)) + list(luar.pertanyaan.head(3)):
            r = rag.jawab(q)
            print(f"\nQ: {q}\nA: {r['teks'] + '  [sumber: ' + ', '.join(r['sumber']) + ']' if r else '(RAG tidak menjawab -> jawaban tetap)'}")


if __name__ == "__main__":
    main()
