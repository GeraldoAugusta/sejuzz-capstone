# Sejuzz AI Services

Layanan AI untuk aplikasi estimasi hasil produksi jus Sejuzz (Capstone Asah 2026, tim A26-CS002).

## Masalah yang diselesaikan
Owner dan karyawan Sejuzz memperkirakan jumlah cup jus dari buah hanya dengan pengalaman, sehingga kebutuhan buah sulit disiapkan dan hasil antar karyawan berbeda. Layanan ini menyelesaikan tiga hal:
1. **Estimasi cup:** rumus menghitung berat kulit, isi, jumlah cup, dan sisa buah dari jenis buah, berat, dan ukuran cup.
2. **Rentang estimasi:** model regresi yield dari data timbang tim Data Science memberi kisaran wajar (persentil 10 sampai 90), bukan satu angka tunggal.
3. **Asisten AI:** pengguna bertanya dengan kalimat bebas ("5 kilo semangka jadi berapa cup large?"). LLM memahami kalimat dan menjelaskan hasil; angka selalu berasal dari rumus, bukan dari LLM. Pertanyaan di luar konteks ditolak dengan sopan.

## Arsitektur
Frontend -> Backend Express -> FastAPI (folder ini). Frontend tidak memanggil layanan ini langsung.
- `POST /api/v1/calculate`: perhitungan estimasi dan rentang.
- `POST /api/v1/ai/explain`: hasil hitung + penjelasan LLM.
- `POST /api/v1/ai/chat`: asisten kalimat bebas (intent: hitung_estimasi, cek_takaran, info_susut_buah, bantuan_penggunaan, out_of_scope).
- Takaran per cup dikirim backend dari database (`gram_per_cup` / `takaran`); takaran bawaan hanya cadangan.
- Dokumentasi interaktif: `/docs` (Swagger). Kontrak lengkap: `docs/KONTRAK_API.md`.

## Fitur generatif (API proprietary)
Google Gemini lewat REST API, dengan prompt terstruktur (instruksi sistem, contoh few-shot, data JSON) di `app/prompts.py` dan `app/nlu.py`. Keluaran LLM divalidasi ulang oleh kode, dan jawaban penjelasan dibuang bila tidak memuat jumlah cup hasil rumus.

## Keandalan
Timeout, retry untuk error sementara (500/503), model cadangan (`LLM_FALLBACK_MODELS`), batas waktu total, dan balasan template bila LLM gagal. Ekstraksi kalimat jatuh ke aturan kata kunci bila LLM tidak bisa dipakai. Input tidak valid dijawab dengan format error seragam `{"error": {"code", "message"}}`.

## Guardrail
Pertanyaan di luar konteks dijawab dengan teks penolakan tetap tanpa memanggil LLM. Hasil uji `scripts/test_guardrail.py` (12 pertanyaan di luar konteks + 4 kontrol):

**TEMPEL tabel hasil dari terminal Anda di sini, lengkap dengan tanggal uji dan model yang dipakai.**

## Model regresi yield (folder `ml/`)
Memperkirakan berat bagian layak dari jenis buah dan berat utuh. Pembagian data 80/20 per buah, cross-validation 5 lipatan untuk memilih model, tuning random forest dengan grid search, data uji dipakai sekali di akhir. Data seimbang (100 sampel per buah).

**TEMPEL isi `ml/output/tabel_perbandingan.md` dari laptop Anda di sini.**

Catatan: data timbang bersifat **simulasi** dan R2 tinggi terutama karena berat layak memang sebanding dengan berat utuh, sehingga model referensi (satu yield untuk semua buah) disertakan sebagai pembanding. Hasil ini menggambarkan data simulasi, bukan akurasi pada buah sungguhan.

## Sumber data dan library
- `data/data_buah_clean.csv`: data timbang buah dari tim Data Science (simulasi, 18 buah x 100 sampel).
- `data/Kalkulator_Yield_Sejuzz.xlsx` dan `data/takaran_per_cup.csv`: rumus dan takaran per cup. Takaran (200 g small, 250 g large) adalah asumsi tim.
- API: Google Gemini (gemini-3.5-flash dengan model cadangan).
- Library layanan: FastAPI, Uvicorn, Pydantic, httpx, python-dotenv (lihat `requirements.txt`). Library eksperimen: pandas, numpy, scikit-learn, matplotlib, joblib (`requirements-ml.txt`).

## Menjalankan
    python3 -m venv .venv && source .venv/bin/activate
    python3 -m pip install -r requirements.txt
    cp .env.example .env        # isi LLM_API_KEY
    python3 -m pytest tests -q
    python3 -m uvicorn app.main:app --reload

## Deploy
- URL: **TEMPEL URL Back4app Anda** (Back4app Containers, tingkat gratis dengan batas jam aktif).
- Semua endpoint `/api/v1/...` wajib header `X-API-Key`; `/health` dan `/docs` terbuka.

## Keterbatasan
Data simulasi, takaran asumsi, penjelasan AI bergantung pada ketersediaan Gemini (ada balasan template sebagai cadangan), dan batas jam gratis hosting.
