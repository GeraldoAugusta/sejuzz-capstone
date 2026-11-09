# Deploy ke Render (tingkat gratis)

Service ini ringan (tanpa library ML), jadi cukup untuk web service gratis Render.

## 0. Struktur repo
Repo tim berisi semua path. Kode AI ada di folder `ai-services/`, jadi di Render **Root Directory harus diisi `ai-services`** (Settings atau Advanced saat membuat service). Dengan itu, Build Command dan Start Command di bawah dijalankan dari dalam folder tersebut.

## 1. Persiapan
- Kode sudah di GitHub, `.env` TIDAK ikut ter-commit.
- `requirements.txt` ada di `ai-services/` (bukan di root repo). `app/data/fruits.json` dan `app/data/yield_per_buah.json` ikut ter-commit.

## 2. Buat Web Service
1. Render, New, Web Service, hubungkan repo GitHub.
2. Root Directory: `ai-services`. Runtime: Python. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Instance Type: Free. Health Check Path: `/health`

## 3. Environment Variables (di dashboard Render, bukan di repo)
| Nama | Isi |
|---|---|
| `PYTHON_VERSION` | `3.12.8` (kode memakai sintaks Python 3.10 ke atas) |
| `LLM_API_KEY` | API key Gemini |
| `LLM_MODEL` | `gemini-3.5-flash` |
| `LLM_FALLBACK_MODELS` | `gemini-3.5-flash-lite,gemini-3.6-flash` |
| `LLM_TIMEOUT_SECONDS` | `20` |
| `LLM_RETRIES` | `2` |
| `LLM_TOTAL_DEADLINE_SECONDS` | `45` |
| `SERVICE_API_KEY` | string acak panjang buatan sendiri; dibagikan ke Nabilla lewat kanal privat |
| `ALLOWED_ORIGINS` | `*` (backend-ke-backend tidak butuh CORS) |

## 4. Uji setelah deploy
- `https://NAMA-SERVICE.onrender.com/health` harus `{"status":"ok"}`.
- `https://NAMA-SERVICE.onrender.com/docs` untuk Swagger (klik Authorize, isi X-API-Key).
- Request tanpa header `X-API-Key` ke `/api/v1/...` harus 401.

## 5. Catatan monorepo
- Auto-deploy memantau seluruh repo, jadi push dari tim Full-stack atau DS bisa ikut memicu deploy ulang. Jika Render menyediakan pengaturan filter build (Build Filters, jalur yang disertakan `ai-services/**`), isi supaya hanya perubahan di folder ini yang memicu deploy. Cek di dashboard karena menu bisa berbeda.
- Jalankan `pytest`, `uvicorn`, dan skrip `scripts/` / `ml/` dari dalam folder `ai-services/`.
- File `.env` dan `.venv/` tidak boleh ter-commit (sudah ada di `ai-services/.gitignore`).

## 6. Catatan penting
- Layanan gratis tidur setelah sekitar 15 menit tanpa permintaan; permintaan pertama setelah tidur lambat (sekitar setengah sampai satu menit). Buka `/health` beberapa menit sebelum demo.
- Jika API key bocor (chat, GitHub, screenshot), hapus dan buat baru.
- Catat URL deploy di README.
