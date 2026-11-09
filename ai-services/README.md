# Sejuzz AI

Folder `ai-services/` pada repo tim. Asisten AI dan modul perhitungan untuk aplikasi estimasi hasil produksi jus Sejuzz (Capstone Asah 2026, A26-CS002).

## Masalah yang diselesaikan
(TODO: isi setelah Tahap 3. Jelaskan masalah yang diselesaikan model AI.)

## Struktur
- `app/` : service FastAPI (rumus, endpoint, nanti LLM)
- `data/` : dataset dari tim Data Science (`data_buah_clean.csv`)
- `scripts/` : skrip pengolah data
- `tests/` : unit test

## Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
pytest -q
uvicorn app.main:app --reload     # Swagger: http://localhost:8000/docs
```

## Sumber data dan library
- Data timbang buah: `data/data_buah_clean.csv` (tim Data Science; 18 buah x 100 sampel, hasil penggabungan dataset per buah). Keterangan nyata/simulasi: TODO konfirmasi DS.
- Takaran per cup: `data/takaran_per_cup.csv`, nilai ASUMSI (200 g Sedang/small dari brief proyek, 250 g Besar/large asumsi tim) dari `data/Kalkulator_Yield_Sejuzz.xlsx`. Ganti bila ada data resep asli Sejuzz, lalu jalankan `python scripts/build_fruit_table.py`.
- Library: lihat `requirements.txt`.
(TODO: lengkapi seiring pengerjaan.)

## Progres checklist
Lihat bagian bawah setelah tiap tahap selesai.

## Asisten AI (alur /api/v1/ai/chat)
1. LLM (Gemini, structured prompt, keluaran JSON) mengekstrak intent dan entitas dari kalimat bebas.
2. Hasil LLM divalidasi ulang oleh kode (`app/nlu.py::normalize`); LLM tidak dipercaya begitu saja.
3. Bila LLM gagal atau keluarannya tidak valid, dipakai ekstraksi aturan kata kunci.
4. Angka jawaban selalu dari rumus/data (`calculator.py`, `fruits.json`), bukan dari LLM.
5. Pertanyaan di luar konteks ditolak dengan jawaban tetap (tanpa LLM). Hasil uji guardrail: jalankan `scripts/test_guardrail.py` lalu tempel tabelnya di sini.

## Model regresi yield (folder ml/)
Tujuan: memperkirakan berat bagian layak dari jenis buah dan berat utuh, serta memberi rentang estimasi cup.
- Data: `data/data_buah_clean.csv` (tim DS, **data simulasi**, 18 buah x 100 sampel). Hasil model menggambarkan data simulasi, bukan akurasi pada buah nyata.
- Preprocessing, pembagian data (80/20 per buah), perbandingan model, dan tuning: `ml/02_latih_bandingkan.py`.
- Jalankan: `pip install -r requirements-ml.txt` lalu `python ml/02_latih_bandingkan.py`.
- Tabel perbandingan (tempel dari `ml/output/tabel_perbandingan.md` hasil jalan Anda): TODO
- Rentang estimasi (P10-P90 yield per buah) tampil di field `rentang` pada `/api/v1/calculate`.
