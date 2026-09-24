import httpx

from app.config import settings


async def notify_admins(text: str) -> None:
    if not settings.BOT_TOKEN or not settings.ADMIN_IDS:
        return
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        for admin_id in settings.ADMIN_IDS:
            try:
                await client.post(url, json={"chat_id": admin_id, "text": text})
            except Exception:
                pass
