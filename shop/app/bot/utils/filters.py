from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.database import get_session
from app.services.users import is_admin, is_owner


class IsAdmin(BaseFilter):
    """Faqat bazadagi adminlar uchun handler ishga tushishini ta'minlaydi.
    Bu tekshiruv HAR DOIM server (bot) tomonida bajariladi - mijoz tomonidan
    aylanib o'tib bo'lmaydi."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        with get_session() as db:
            return is_admin(db, user.id)


class IsOwner(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        with get_session() as db:
            return is_owner(db, user.id)
