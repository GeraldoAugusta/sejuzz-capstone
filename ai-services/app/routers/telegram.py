from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header
from fastapi.responses import JSONResponse

from app.kanal import telegram
from app.security import verify_api_key

router = APIRouter(prefix="/kanal/telegram", tags=["Kanal Telegram"])


@router.post("/webhook", include_in_schema=True, summary="Webhook Telegram (dipanggil Telegram, bukan backend)")
def webhook(background: BackgroundTasks, update: dict = Body(...),
            x_telegram_bot_api_secret_token: Optional[str] = Header(None)):
    """Dilindungi header rahasia dari Telegram (bukan X-API-Key). Balas 200 segera, jawaban diproses di latar belakang."""
    if not telegram.rahasia_valid(x_telegram_bot_api_secret_token):
        return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": "Rahasia webhook tidak valid."}})
    background.add_task(telegram.proses_update, update)
    return {"ok": True}


@router.get("/status", dependencies=[Depends(verify_api_key)], summary="Cek konfigurasi kanal (tanpa membuka rahasia)")
def status():
    import os
    return {"token_terpasang": bool(os.getenv("TELEGRAM_BOT_TOKEN")), "rahasia_terpasang": bool(os.getenv("TELEGRAM_WEBHOOK_SECRET")),
            "daftar_izin_aktif": bool(os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip())}
