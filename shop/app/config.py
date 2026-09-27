"""
Loyihaning barcha sozlamalari shu yerda, environment variables orqali olinadi.
Hech qanday token yoki maxfiy ma'lumot kod ichida ochiq yozilmagan.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Majburiy sozlamalar (.env faylida to'ldiriladi) ---
    BOT_TOKEN: str = ""              # BotFather'dan olingan token
    OWNER_TELEGRAM_ID: int = 0       # Bot egasining Telegram ID raqami (birinchi admin)

    # --- Ixtiyoriy / keyinroq sozlanadigan qiymatlar ---
    WEBSITE_URL: str = ""            # Web-sayt manzili (hosting qilingandan keyin shu yerga yoziladi)
    DATABASE_URL: str = "sqlite:///./shop.db"

    # API (kelajakda web-sayt shu API bilan gaplashadi)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
