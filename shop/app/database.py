"""
Bitta umumiy ma'lumotlar bazasi ulanishi.
Bot ham, kelajakdagi API ham xuddi shu Session'dan foydalanadi -
shuning uchun ikkalasi ham bir xil ma'lumotni ko'radi.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


@contextmanager
def get_session():
    """Har bir operatsiya uchun xavfsiz session ochib-yopib beradi."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Barcha jadvallarni (agar mavjud bo'lmasa) yaratadi."""
    from app import models  # noqa
    Base.metadata.create_all(bind=engine)
