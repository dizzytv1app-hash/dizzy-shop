from sqlalchemy.orm import Session
from app.models import Setting

# Ishlatiladigan kalitlar
KEY_HELP_CHAT_ID = "help_chat_id"
KEY_CHANNEL_ID = "channel_id"
KEY_CARD_NUMBER = "card_number"
KEY_CARD_OWNER = "card_owner"


def get_setting(db: Session, key: str) -> str | None:
    row = db.query(Setting).filter(Setting.key == key).one_or_none()
    return row.value if row else None


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(Setting).filter(Setting.key == key).one_or_none()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
