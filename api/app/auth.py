"""
Ikki xil autentifikatsiya bor:

1. Admin (botdan keladigan so'rovlar) — header orqali:
   X-Bot-Secret: BOT_API_SECRET bilan bir xil
   X-Admin-Id:   Telegram ID, ADMIN_IDS ro'yxatida bo'lishi shart

2. Oddiy foydalanuvchi (mini appdan keladigan so'rovlar) — header orqali:
   X-Telegram-Init-Data: Telegram.WebApp.initData qiymati (frontend hech narsa
   o'zgartirmasdan shu qatorni yuboradi). Backend buni bot tokeni bilan
   HMAC-SHA256 orqali tekshiradi — shu tekshiruvdan o'tmagan so'rov rad etiladi.
   Frontenddan kelgan "telegram_id"ga hech qachon ishonilmaydi — faqat shu
   tekshiruvdan chiqqan id ishlatiladi.
"""

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from app.config import settings


def require_admin(x_bot_secret: str = Header(default=""), x_admin_id: str = Header(default="")) -> int:
    if x_bot_secret != settings.BOT_API_SECRET:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Noto'g'ri bot sir kodi")
    if not x_admin_id.isdigit() or int(x_admin_id) not in settings.ADMIN_IDS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bu ID admin emas")
    return int(x_admin_id)


def _validate_init_data(init_data: str) -> dict:
    """Telegram hujjatlashtirilgan algoritm: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app"""
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "initData imzosi yo'q")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "initData imzosi noto'g'ri")

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Foydalanuvchi topilmadi")
    return json.loads(user_raw)


def get_current_user(x_telegram_init_data: str = Header(default="")) -> dict:
    if settings.DEV_SKIP_TELEGRAM_AUTH:
        # Faqat lokal test uchun: ?debug_user_id= headeri kabi ishlatiladi
        return {"id": int(x_telegram_init_data or 0) or 999999, "username": "dev", "first_name": "Dev"}

    if not x_telegram_init_data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-Telegram-Init-Data header yo'q")
    try:
        return _validate_init_data(x_telegram_init_data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "initData ni o'qib bo'lmadi")
