# Kanal Telegram untuk Asisten Sejuzz

Pengguna (owner atau karyawan) bertanya lewat Telegram; jawabannya sama dengan `/api/v1/ai/chat` (classifier intent, rumus, RAG, guardrail).

## Cara kerja

Telegram memanggil `POST /kanal/telegram/webhook` di service ini. Header `X-Telegram-Bot-Api-Secret-Token` harus sama dengan `TELEGRAM_WEBHOOK_SECRET` (bukan `X-API-Key`). Service membalas 200 segera, lalu memproses jawaban di latar belakang dan mengirimnya lewat Bot API.

## Pengaturan

1. Di Telegram, buka @BotFather, kirim `/newbot`, isi nama dan username (diakhiri `bot`). Simpan token yang diberikan; token adalah kunci, jangan dibagikan.
2. Buat rahasia webhook: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Isi variabel lingkungan di `.env` (lokal) dan di dashboard Back4app:

| Variabel                      | Isi                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN`          | token dari BotFather                                                          |
| `TELEGRAM_WEBHOOK_SECRET`     | rahasia dari langkah 2 (wajib; bila kosong semua webhook ditolak)             |
| `TELEGRAM_ALLOWED_CHAT_IDS`   | opsional, ID chat yang boleh memakai bot, dipisah koma (kosong = semua boleh) |
| `TELEGRAM_RATE_LIMIT_PER_MIN` | opsional, batas pesan per chat per menit (bawaan 10)                          |

4. Deploy ulang, lalu pasang webhook (dari komputer, `.env` berisi token dan rahasia yang sama):
   `python3 scripts/atur_webhook_telegram.py --url https://NAMA.back4app.app`
5. Cek: `python3 scripts/atur_webhook_telegram.py --info` (URL harus terisi dan error terakhir `-`).
6. Kirim pesan ke bot. Perintah: `/start`, `/help`, `/id` (menampilkan ID chat untuk daftar izin).

## Batasan (jujur)

- Hanya chat pribadi dan pesan teks; grup, foto, dan stiker diabaikan atau dijawab sopan.
- Takaran per cup memakai takaran bawaan service, bukan takaran terbaru dari database backend.
- Batas laju dan anti pesan ganda tersimpan di memori satu proses; ikut hilang saat container restart.
- Bot yang username-nya diketahui orang lain bisa dipakai siapa saja kecuali `TELEGRAM_ALLOWED_CHAT_IDS` diisi; setiap pesan memakai kuota Gemini.
- Container gratis bisa tidur; pesan pertama setelah lama diam bisa lambat dan Telegram akan mencoba mengirim ulang.
- Percakapan tidak disimpan oleh service ini.
