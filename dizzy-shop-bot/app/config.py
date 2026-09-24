import os
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> set[int]:
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://example.vercel.app")
    ADMIN_IDS: set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    BOT_API_SECRET: str = os.getenv("BOT_API_SECRET", "change-me")
    SHOP_NAME: str = os.getenv("SHOP_NAME", "Dizzy Shop")


settings = Settings()
