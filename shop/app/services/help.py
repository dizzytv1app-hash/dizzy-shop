from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import HelpRequest, User

RATE_LIMIT_HOURS = 5


def can_send_help(db: Session, user: User) -> tuple[bool, int]:
    """Foydalanuvchi yana qancha daqiqadan keyin murojaat yubora olishini qaytaradi."""
    last = (
        db.query(HelpRequest)
        .filter(HelpRequest.user_id == user.id)
        .order_by(HelpRequest.created_at.desc())
        .first()
    )
    if not last:
        return True, 0
    elapsed = datetime.utcnow() - last.created_at
    limit = timedelta(hours=RATE_LIMIT_HOURS)
    if elapsed >= limit:
        return True, 0
    remaining_minutes = int((limit - elapsed).total_seconds() // 60) + 1
    return False, remaining_minutes


def create_help_request(db: Session, user: User, text: str | None, photo_file_id: str | None) -> HelpRequest:
    req = HelpRequest(user_id=user.id, text=text, photo_file_id=photo_file_id)
    db.add(req)
    db.flush()
    return req
