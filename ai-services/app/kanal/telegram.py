"""Adaptor Telegram (webhook). Pesan teks pribadi dijawab oleh chat.handle_message.

Pengaturan (environment): TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET (wajib, bila kosong semua webhook ditolak),
TELEGRAM_ALLOWED_CHAT_IDS (opsional, daftar id dipisah koma; kosong = semua boleh), TELEGRAM_RATE_LIMIT_PER_MIN (bawaan 10).
Takaran memakai takaran bawaan service (backend tidak ikut mengirim takaran lewat kanal ini).
"""
import logging
import os
import secrets

import httpx

from app.kanal import inti

log = logging.getLogger("sejuzz.telegram")
API = "https://api.telegram.org"
_BATAS = inti.BatasLaju(maks=int(os.getenv("TELEGRAM_RATE_LIMIT_PER_MIN", "10")))
_DEDUP = inti.AntiGanda()


def _token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def rahasia_valid(header) -> bool:
    """Webhook sah hanya bila header X-Telegram-Bot-Api-Secret-Token sama dengan TELEGRAM_WEBHOOK_SECRET."""
    rahasia = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    return bool(rahasia) and bool(header) and secrets.compare_digest(str(header), rahasia)


def diizinkan(id_chat) -> bool:
    daftar = {x.strip() for x in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if x.strip()}
    return not daftar or str(id_chat) in daftar


def kirim_pesan(id_chat, teks: str) -> bool:
    """Kirim balasan lewat Bot API. Tidak pernah melempar error; mengembalikan True bila terkirim."""
    if not _token():
        log.warning("TELEGRAM_BOT_TOKEN belum diisi, balasan tidak dikirim")
        return False
    try:
        r = httpx.post(f"{API}/bot{_token()}/sendMessage", json={"chat_id": id_chat, "text": teks[:4000]}, timeout=15)
        if r.status_code != 200:
            log.warning("sendMessage gagal, status %s", r.status_code)  # token tidak dicatat
        return r.status_code == 200
    except httpx.HTTPError as e:
        log.warning("sendMessage gagal: %s", type(e).__name__)
        return False


def proses_update(update: dict, kirim=None) -> str:
    """Proses satu update. Kembalikan status singkat (berguna untuk tes dan log)."""
    kirim = kirim or kirim_pesan
    uid = update.get("update_id")
    if uid is not None and not _DEDUP.baru(uid):
        return "duplikat"
    msg = update.get("message")
    if not isinstance(msg, dict):
        return "diabaikan_bukan_pesan"
    chat_info = msg.get("chat") or {}
    cid = chat_info.get("id")
    if cid is None or chat_info.get("type") != "private":
        return "diabaikan_bukan_privat"
    if not diizinkan(cid):
        log.info("chat tidak diizinkan: %s", cid)
        kirim(cid, "Maaf, bot ini hanya untuk pengguna Sejuzz yang terdaftar.")
        return "ditolak_izin"
    teks = msg.get("text")
    if not teks:
        kirim(cid, "Maaf, aku hanya bisa membaca pesan teks.")
        return "diabaikan_bukan_teks"
    if not _BATAS.izinkan(cid):
        kirim(cid, "Terlalu banyak pesan dalam waktu singkat. Tunggu semenit lalu coba lagi ya.")
        return "dibatasi"
    try:
        kirim(cid, inti.balasan(teks, cid))
        return "dibalas"
    except Exception:  # satu pesan bermasalah tidak boleh mematikan webhook
        log.exception("gagal memproses pesan")
        try:
            kirim(cid, "Maaf, ada gangguan saat memproses pesanmu. Coba lagi sebentar ya.")
        except Exception:
            pass
        return "error"
