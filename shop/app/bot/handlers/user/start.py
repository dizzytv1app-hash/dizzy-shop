from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import get_session
from app.services.users import get_or_create_user, is_admin
from app.bot.keyboards import main_user_keyboard
from app.config import settings

router = Router(name="start")


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject, state: FSMContext):
    payload = command.args or ""
    with get_session() as db:
        get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.full_name)

    if payload.startswith("order_"):
        code = payload.removeprefix("order_").upper()
        from app.bot.handlers.user.order_flow import begin_order
        await message.answer("👋 Xush kelibsiz! Buyurtmangizni davom ettiramiz.")
        await begin_order(message, state, code)
        return

    await cmd_start(message)


@router.message(CommandStart())
async def cmd_start(message: Message):
    with get_session() as db:
        get_or_create_user(
            db, message.from_user.id, message.from_user.username, message.from_user.full_name
        )
        admin = is_admin(db, message.from_user.id)

    text = (
        "👋 Assalomu alaykum, xush kelibsiz!\n\n"
        "Bu — zamonaviy kiyimlar do'koni boti. Bu yerda yangi mahsulotlar, chegirmalar "
        "haqida bilib borishingiz va buyurtma berishingiz mumkin."
    )
    if not settings.WEBSITE_URL:
        text += "\n\n⚠️ Web-sayt hali ulanmagan. Tez orada shu yerga qo'shiladi."
    if admin:
        text += "\n\nSiz admin sifatida ro'yxatdan o'tgansiz. Admin panelini ochish uchun /admin buyrug'ini yuboring."

    await message.answer(text, reply_markup=main_user_keyboard())
