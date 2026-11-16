"""Atur webhook Telegram. Jalankan dari folder ai-services/ (butuh TELEGRAM_BOT_TOKEN dan TELEGRAM_WEBHOOK_SECRET di .env):

    python3 scripts/atur_webhook_telegram.py --url https://NAMA.back4app.app    # pasang webhook
    python3 scripts/atur_webhook_telegram.py --info                              # lihat status dan error terakhir
    python3 scripts/atur_webhook_telegram.py --hapus                             # lepas webhook

Token dan rahasia tidak pernah dicetak.
"""
import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
RAHASIA = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
API = "https://api.telegram.org"


def panggil(metode, **json):
    r = httpx.post(f"{API}/bot{TOKEN}/{metode}", json=json, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "description": f"respons bukan JSON (status {r.status_code})"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--hapus", action="store_true")
    a = ap.parse_args()
    if not TOKEN:
        sys.exit("GAGAL: TELEGRAM_BOT_TOKEN belum diisi di .env")
    if a.info:
        h = panggil("getWebhookInfo").get("result", {})
        print("URL webhook:", h.get("url") or "(belum dipasang)")
        print("Update menunggu:", h.get("pending_update_count"))
        print("Error terakhir:", h.get("last_error_message") or "-")
    elif a.hapus:
        print(panggil("deleteWebhook", drop_pending_updates=True))
    elif a.url:
        if not RAHASIA:
            sys.exit("GAGAL: TELEGRAM_WEBHOOK_SECRET belum diisi di .env (1-256 karakter A-Z a-z 0-9 _ -)")
        if not a.url.startswith("https://"):
            sys.exit("GAGAL: URL harus https://")
        tujuan = a.url.rstrip("/") + "/kanal/telegram/webhook"
        hasil = panggil("setWebhook", url=tujuan, secret_token=RAHASIA, allowed_updates=["message"], drop_pending_updates=True)
        print("Tujuan:", tujuan)
        print("Hasil:", hasil.get("ok"), "-", hasil.get("description"))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
