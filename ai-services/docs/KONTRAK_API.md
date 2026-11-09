# Kontrak API Sejuzz AI Service (draf untuk disepakati dengan tim Full-stack)

Base URL lokal: `http://localhost:8000` (URL deploy menyusul). Swagger: `/docs`.
Semua request/response JSON. Pada service yang di-deploy, semua endpoint `/api/v1/...` wajib header `X-API-Key: <kunci>` (dibagikan lewat kanal privat); tanpa itu response 401 `UNAUTHORIZED`. `/health` dan `/docs` tetap terbuka. Frontend sebaiknya memanggil lewat backend (Express), bukan langsung ke service ini.

## Format error seragam
```json
{"error": {"code": "FRUIT_NOT_FOUND", "message": "Buah 'durian' belum ada di data takaran."}}
```
| Status | code | Arti |
|---|---|---|
| 400 | `INVALID_AMOUNT`, `INVALID_UNIT`, `INVALID_CUP_SIZE`, `TAKARAN_NOT_SET`, `INVALID_SUSUT`, `EMPTY_MESSAGE` | Input tidak valid / data belum lengkap |
| 404 | `FRUIT_NOT_FOUND` | Buah tidak ada di data |
| 401 | `UNAUTHORIZED` | Header X-API-Key tidak ada atau salah (hanya bila service memakai SERVICE_API_KEY) |
| 422 | `VALIDATION_ERROR` | Bentuk request salah (field hilang, tipe salah) |

## GET /health
`{"status": "ok"}`

## GET /api/v1/fruits
`{"fruits": ["alpukat", "blackberry", "..."]}` (18 buah, huruf kecil)

## POST /api/v1/calculate
Request:
```json
{"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small", "gram_per_cup": 200}
```
- `unit`: `kg` atau `buah`. `cup_size`: `small` (menu: Sedang) atau `large` (menu: Besar).
- `gram_per_cup` opsional. Bila diisi, menimpa takaran bawaan service (cara backend mengirim takaran dari databasenya).

Response 200:
```json
{"fruit": "semangka", "cup_size": "small", "berat_total_gram": 10000.0, "berat_kulit_gram": 4890.0,
 "berat_isi_gram": 5110.0, "gram_per_cup": 200.0, "jumlah_cup": 25, "sisa_buah_gram": 110.0,
 "rentang": {"cup_min": 23, "cup_max": 28, "isi_gram_min": 4660.0, "isi_gram_max": 5610.0,
             "persentil": "P10-P90", "jenis_data": "simulasi"}}
```
`rentang` bersifat **opsional** (boleh diabaikan UI; bernilai `null` bila data sebaran tidak tersedia). Isinya kisaran wajar jumlah cup dari sebaran yield per buah. `jenis_data` = `simulasi` selama data timbang nyata belum ada, sebaiknya ditampilkan sebagai catatan di UI ("estimasi berdasarkan data simulasi").

## POST /api/v1/ai/explain
Request: sama dengan `/calculate`. Response 200:
```json
{"calculation": { "...sama dengan response /calculate..." },
 "explanation": "Dari 10 kg semangka kamu bisa dapat sekitar 25 cup small ...",
 "source": "llm", "model": "gemini-3.5-flash"}
```
`source`: `llm` atau `fallback` (template saat AI gagal). Angka di `calculation` selalu dari rumus.

## POST /api/v1/ai/chat
Request (frontend hanya mengirim `message` ke backend; backend menambahkan `takaran` dari PostgreSQL sebelum meneruskan ke service):
```json
{"message": "5 kilo semangka jadi berapa cup large?",
 "takaran": {"semangka": {"small": 200, "large": 250}, "melon": {"small": 200, "large": 250}}}
```
- `message`: 1 sampai 300 karakter, wajib.
- `takaran` (opsional, diisi backend): gram per cup per buah. Nama buah huruf kecil sama dengan `GET /api/v1/fruits`; ukuran hanya `small` / `large`; nilai harus > 0, bila tidak valid response 422. Takaran ini **selalu diutamakan** untuk perhitungan dan jawaban "takaran berapa"; takaran bawaan service hanya cadangan bila tidak dikirim.
- Susut/yield buah tetap dari data di service (bukan dari backend).
- Sapaan seperti "halo" dijawab ramah (`status: answered`, `intent: bantuan_penggunaan`); pertanyaan di luar topik jus dijawab `status: refused`.

Response 200:
```json
{"intent": "hitung_estimasi", "status": "answered", "reply": "Dari 5 kg semangka ...",
 "calculation": {"...": "..."}, "missing": [],
 "extraction": {"fruit": "semangka", "amount": 5.0, "unit": "kg", "cup_size": "large"},
 "extraction_source": "llm", "explanation_source": "llm", "model": "gemini-3.5-flash"}
```
- `intent`: `hitung_estimasi`, `cek_takaran`, `info_susut_buah`, `bantuan_penggunaan`, `out_of_scope`.
- `status`: `answered` (tampilkan `reply`), `need_more_info` (tampilkan `reply`, `missing` berisi field yang kurang: `fruit`, `amount`, `unit`, `cup_size`), `refused` (di luar konteks, tampilkan `reply`).
- `calculation` hanya terisi bila `intent` = `hitung_estimasi` dan `status` = `answered`.
- UI cukup menampilkan `reply` sebagai balasan chat; `calculation` opsional untuk menampilkan rincian.

## Keputusan yang sudah disepakati dengan Full-stack (Nabilla)
1. Takaran per cup dibaca dari PostgreSQL oleh backend dan dikirim: `gram_per_cup` pada `/calculate` dan `/ai/explain`, `takaran` pada `/ai/chat`.
2. Ukuran cup di UI: "Sedang" = `small`, "Besar" = `large`.
3. Alur: Frontend, lalu Backend Express, lalu FastAPI. Frontend tidak memanggil service langsung.
4. Panel chat di UI: kirim `message`, tampilkan `reply`.
