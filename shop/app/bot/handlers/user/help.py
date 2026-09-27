from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import get_session
from app.services.users import get_or_create_user
from app.services.help import can_send_help, create_help_request
from app.services.settings_service import get_setting, KEY_HELP_CHAT_ID
from app.bot.states import HelpRequestFlow
from app.bot.keyboards import cancel_keyboard

router = Router(name="help")


@router.message(Command("help"), StateFilter(None))
async def cmd_help(message: Message, state: FSMContext):
    with get_session() as db:
        user = get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.full_name)
        allowed, wait_minutes = can_send_help(db, user)

    if not allowed:
        await message.answer(
            f"⏳ Siz yaqinda murojaat yubordingiz. Keyingi murojaat uchun "
            f"taxminan {wait_minutes} daqiqadan so'ng qayta urinib ko'ring."
        )
        return

    await state.set_state(HelpRequestFlow.waiting_message)
    await message.answer(
        "✍️ Savol, muammo yoki takliflaringizni yozing. Rasm ham biriktirishingiz mumkin.\n"
        "Yuborilgandan so'ng bizning jamoamiz tez orada javob beradi.",
        reply_markup=cancel_keyboard(),
    )


@router.message(HelpRequestFlow.waiting_message, F.text == "🚫 Bekor qilish")
async def help_cancel(message: Message, state: FSMContext):
    from app.bot.keyboards import main_user_keyboard
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_user_keyboard())


@router.message(HelpRequestFlow.waiting_message)
async def help_receive(message: Message, state: FSMContext, bot):
    text = message.text or message.caption
    photo_file_id = message.photo[-1].file_id if message.photo else None

    if not text and not photo_file_id:
        await message.answer("Iltimos, matn yozing yoki rasm yuboring.")
        return

    with get_session() as db:
        user = get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.full_name)
        allowed, wait_minutes = can_send_help(db, user)
        if not allowed:
            await state.clear()
            await message.answer(f"⏳ Bu oraliqda faqat bitta murojaat yuborish mumkin edi. "
                                  f"{wait_minutes} daqiqadan so'ng qayta urinib ko'ring.")
            return

        create_help_request(db, user, text, photo_file_id)
        help_chat_id = get_setting(db, KEY_HELP_CHAT_ID)
        username = message.from_user.username
        full_name = message.from_user.full_name
        tg_id = message.from_user.id

    await state.clear()
    from app.bot.keyboards import main_user_keyboard
    await message.answer("✅ Murojaatingiz qabul qilindi. Tez orada javob beramiz.",
                          reply_markup=main_user_keyboard())

    if not help_chat_id:
        return  # Admin hali help chatni ulamagan - murojaat faqat bazada saqlanadi

    profile_link = f"@{username}" if username else f'<a href="tg://user?id={tg_id}">profil</a>'
    caption = (
        f"📩 Yangi murojaat\n"
        f"Foydalanuvchi: {profile_link}\n"
        f"Ism: {full_name or '-'}\n"
        f"Telegram ID: <code>{tg_id}</code>\n\n"
        f"{text or ''}"
    )
    try:
        if photo_file_id:
            await bot.send_photo(chat_id=int(help_chat_id), photo=photo_file_id, caption=caption)
        else:
            await bot.send_message(chat_id=int(help_chat_id), text=caption)
    except Exception:
        # Chat ID noto'g'ri yoki bot u yerda admin emas bo'lishi mumkin - buni logga yozamiz
        import logging
        logging.exception("Help chatga xabar yuborib bo'lmadi")
