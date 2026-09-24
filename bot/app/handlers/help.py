from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.states import HelpForm
from app.api_client import create_support_ticket, ApiError

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.set_state(HelpForm.waiting_message)
    await message.answer(
        "🆘 Nimadir ishlamayaptimi?\n\n"
        "Muammoni matn bilan yozing yoki skrinshot/rasm yuboring — "
        "to'g'ridan-to'g'ri adminga yetkazamiz."
    )


@router.message(StateFilter(HelpForm.waiting_message), F.photo)
async def help_photo(message: Message, state: FSMContext, bot):
    caption = message.caption or "(izohsiz rasm)"
    await _dispatch(message, bot, text=caption, photo_file_id=message.photo[-1].file_id)
    await state.clear()


@router.message(StateFilter(HelpForm.waiting_message), F.text)
async def help_text(message: Message, state: FSMContext, bot):
    await _dispatch(message, bot, text=message.text, photo_file_id=None)
    await state.clear()


async def _dispatch(message: Message, bot, text: str, photo_file_id: str | None):
    user = message.from_user
    username = f"@{user.username}" if user.username else user.full_name

    admin_text = f"🆘 Yangi yordam so'rovi\nFoydalanuvchi: {username} (ID: {user.id})\n\n{text}"
    for admin_id in settings.ADMIN_IDS:
        try:
            if photo_file_id:
                await bot.send_photo(admin_id, photo_file_id, caption=admin_text)
            else:
                await bot.send_message(admin_id, admin_text)
        except Exception:
            pass

    try:
        await create_support_ticket(user_id=user.id, username=username, message=text, photo_file_id=photo_file_id)
    except ApiError:
        pass

    await message.answer("Xabaringiz qabul qilindi ✅ Tez orada javob beramiz.")
