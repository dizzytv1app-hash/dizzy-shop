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
    # PostgreSQL ulanish manzili: postgresql://user:pass@host:5432/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dizzy_shop")

    # Bot bilan bir xil bo'lishi shart
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

    # Bot -> API so'rovlarida tekshiriladigan umumiy sir
    BOT_API_SECRET: str = os.getenv("BOT_API_SECRET", "change-me")

    # Mini App (brauzer) qaysi domendan so'rov yuborishi mumkin
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]

    # Telegram WebApp initData imzosini tekshirmaslik (faqat lokal test uchun!)
    DEV_SKIP_TELEGRAM_AUTH: bool = os.getenv("DEV_SKIP_TELEGRAM_AUTH", "false").lower() == "true"

    SHOP_NAME: str = os.getenv("SHOP_NAME", "Dizzy Shop")


settings = Settings()
