from sqlalchemy.orm import Session
from app.models import User, Admin


def get_or_create_user(db: Session, telegram_id: int, username: str | None, full_name: str | None) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        db.add(user)
        db.flush()
    else:
        # Profil o'zgargan bo'lishi mumkin - yangilab qo'yamiz
        user.username = username
        user.full_name = full_name
    return user


def is_admin(db: Session, telegram_id: int) -> bool:
    return db.query(Admin).filter(Admin.telegram_id == telegram_id).first() is not None


def is_owner(db: Session, telegram_id: int) -> bool:
    admin = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    return bool(admin and admin.is_owner)


def add_admin(db: Session, telegram_id: int, username: str | None, added_by: int) -> tuple[bool, str]:
    existing = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    if existing:
        return False, "Bu foydalanuvchi allaqachon admin."
    admin = Admin(telegram_id=telegram_id, username=username, is_owner=False, added_by=added_by)
    db.add(admin)
    return True, "Admin muvaffaqiyatli qo'shildi."


def remove_admin(db: Session, telegram_id: int, requester_id: int) -> tuple[bool, str]:
    target = db.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    if not target:
        return False, "Bunday admin topilmadi."
    if target.is_owner:
        return False, "Bot egasini o'chirib bo'lmaydi."
    db.delete(target)
    return True, "Admin o'chirildi."


def list_admins(db: Session) -> list[Admin]:
    return db.query(Admin).order_by(Admin.is_owner.desc(), Admin.created_at).all()


def ensure_owner_bootstrapped(db: Session, owner_telegram_id: int):
    """Bot birinchi marta ishga tushganda, .env dagi OWNER_TELEGRAM_ID ni asosiy admin qilib qo'yadi."""
    if not owner_telegram_id:
        return
    existing = db.query(Admin).filter(Admin.telegram_id == owner_telegram_id).first()
    if existing:
        if not existing.is_owner:
            existing.is_owner = True
        return
    db.add(Admin(telegram_id=owner_telegram_id, is_owner=True))
