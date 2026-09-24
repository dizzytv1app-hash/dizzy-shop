from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.keyboards import open_shop_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        f"Salom, {message.from_user.first_name}! 👋\n\n"
        f"<b>{settings.SHOP_NAME}</b>ga xush kelibsiz — zamonaviy kiyim-kechak do'koni.\n"
        "Bu yerda kiyim, anime, gaming, streetwear, poyabzal va aksessuarlarni topasiz.\n\n"
        "Do'konni ochish uchun pastdagi tugmani bosing 👇\n\n"
        "Yordam kerak bo'lsa — /help"
    )
    await message.answer(text, reply_markup=open_shop_keyboard())


@router.message(F.text == "🛍️ Do'konni ochish")
async def reopen_shop(message: Message):
    await message.answer("Do'konni ochish uchun pastdagi tugmadan foydalaning 👇", reply_markup=open_shop_keyboard())
