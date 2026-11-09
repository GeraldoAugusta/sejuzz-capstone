"""Structured prompt: instruksi sistem + few-shot + data terstruktur.

Prinsip: LLM hanya MENJELASKAN angka yang sudah dihitung rumus. LLM tidak boleh menghitung ulang.
"""
import json

SYSTEM = """Kamu adalah Asisten Sejuzz, asisten untuk kedai jus buah Sejuzz.
Tugasmu: menjelaskan hasil perhitungan estimasi cup jus kepada owner atau karyawan.

Aturan:
1. Pakai HANYA angka dari bagian DATA. Jangan menghitung ulang, membulatkan ulang, atau menambah angka baru.
2. Tulis dalam Bahasa Indonesia santai dan ramah, 2 sampai 4 kalimat, tanpa tabel atau daftar.
3. Sebut jenis buah, jumlah cup, ukuran cup, dan sisa buah.
4. Jangan membahas hal di luar estimasi cup jus (harga, untung, stok, resep lain).
5. Ingatkan singkat bahwa ini estimasi, hasil nyata bisa sedikit berbeda."""

FEW_SHOT = [
    {
        "data": {"buah": "semangka", "input": "10 kg", "ukuran_cup": "small", "berat_isi_gram": 5110.0,
                 "gram_per_cup": 200.0, "jumlah_cup": 25, "sisa_buah_gram": 110.0},
        "jawaban": "Dari 10 kg semangka, kamu bisa dapat sekitar 25 cup small ya. Masih ada sisa daging buah sekitar 110 gram, "
                   "belum cukup untuk satu cup lagi. Ini estimasi, jadi hasil nyatanya bisa sedikit berbeda.",
    },
    {
        "data": {"buah": "tomat", "input": "0.1 kg", "ukuran_cup": "small", "berat_isi_gram": 91.45,
                 "gram_per_cup": 200.0, "jumlah_cup": 0, "sisa_buah_gram": 91.45},
        "jawaban": "Dengan 0.1 kg tomat, belum cukup untuk satu cup small, jadi hasilnya 0 cup. "
                   "Daging buah yang bisa dipakai sekitar 91,45 gram. Tambah buahnya dulu ya. Ini hanya estimasi.",
    },
]


def build_prompt(calc: dict, amount, unit: str) -> str:
    def fmt(c):
        return json.dumps(c, ensure_ascii=False)

    parts = ["Berikut contoh gaya jawaban:\n"]
    for ex in FEW_SHOT:
        parts.append(f"DATA: {fmt(ex['data'])}\nJAWABAN: {ex['jawaban']}\n")
    data = {
        "buah": calc["fruit"], "input": f"{amount:g} {unit}", "ukuran_cup": calc["cup_size"],
        "berat_isi_gram": calc["berat_isi_gram"], "gram_per_cup": calc["gram_per_cup"],
        "jumlah_cup": calc["jumlah_cup"], "sisa_buah_gram": calc["sisa_buah_gram"],
    }
    parts.append(f"Sekarang jelaskan data ini dengan gaya yang sama.\nDATA: {fmt(data)}\nJAWABAN:")
    return "\n".join(parts)
