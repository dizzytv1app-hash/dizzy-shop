from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import get_session
from app.services.settings_service import (
    set_setting, get_setting, KEY_HELP_CHAT_ID, KEY_CHANNEL_ID, KEY_CARD_NUMBER, KEY_CARD_OWNER,
)
from app.bot.utils.filters import IsAdmin
from app.bot.keyboards import cancel_keyboard, admin_main_menu
from app.bot.states import HelpChatSetup, ChannelSetup, CardSetup

router = Router(name="settings")


# ---------- Help chatini ulash ----------

@router.message(F.text == "💬 Help chatini ulash", IsAdmin(), StateFilter(None))
async def start_help_chat_setup(message: Message, state: FSMContext):
    with get_session() as db:
        current = get_setting(db, KEY_HELP_CHAT_ID)
    txt = f"Hozirgi help chat ID: <code>{current}</code>\n\n" if current else ""
    await state.set_state(HelpChatSetup.waiting_chat_id)
    await message.answer(
        f"{txt}Botni admin sifatida qo'shgan guruh/chatingizning ID raqamini yuboring.\n"
        f"(ID ni olish uchun @userinfobot yoki @getmyid_bot kabi botlardan foydalanishingiz mumkin, "
        f"odatda manfiy raqam bo'ladi, masalan -1001234567890)",
        reply_markup=cancel_keyboard(),
    )


@router.message(HelpChatSetup.waiting_chat_id, F.text == "🚫 Bekor qilish")
@router.message(ChannelSetup.waiting_channel_id, F.text == "🚫 Bekor qilish")
@router.message(CardSetup.waiting_card_number, F.text == "🚫 Bekor qilish")
@router.message(CardSetup.waiting_card_owner, F.text == "🚫 Bekor qilish")
async def cancel_settings(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(HelpChatSetup.waiting_chat_id)
async def save_help_chat(message: Message, state: FSMContext, bot):
    raw = (message.text or "").strip()
    try:
        chat_id = int(raw)
    except ValueError:
        await message.answer("ID faqat raqam bo'lishi kerak (manfiy bo'lishi mumkin). Qaytadan kiriting:")
        return

    try:
        await bot.send_message(chat_id, "✅ Bu chat do'kon botining help-chat sifatida ulandi.")
    except Exception:
        await message.answer(
            "⚠️ Botga bu chatga xabar yubora olmadim. Iltimos, botni shu chatga admin qilib qo'shganingizga "
            "ishonch hosil qiling va ID ni qayta yuboring."
        )
        return

    with get_session() as db:
        set_setting(db, KEY_HELP_CHAT_ID, str(chat_id))
    await state.clear()
    await message.answer("✅ Help chat muvaffaqiyatli ulandi.", reply_markup=admin_main_menu())


# ---------- Kanalga ulash ----------

@router.message(F.text == "📤 Kanalga yuborish", IsAdmin(), StateFilter(None))
async def open_channel_menu(message: Message, state: FSMContext):
    with get_session() as db:
        channel_id = get_setting(db, KEY_CHANNEL_ID)
    if not channel_id:
        await state.set_state(ChannelSetup.waiting_channel_id)
        await message.answer(
            "Avval kanal ulanmagan. Botni admin qilib qo'shgan kanalingizning ID raqamini yuboring "
            "(masalan -1001234567890):",
            reply_markup=cancel_keyboard(),
        )
        return
    # Kanal ulangan bo'lsa - mahsulot kodini so'raymiz (send_to_channel.py da davom etadi)
    from app.bot.states import SendToChannel
    await state.set_state(SendToChannel.waiting_code)
    await message.answer("Kanalga yubormoqchi bo'lgan mahsulot kodini kiriting:", reply_markup=cancel_keyboard())


@router.message(ChannelSetup.waiting_channel_id)
async def save_channel(message: Message, state: FSMContext, bot):
    raw = (message.text or "").strip()
    try:
        chat_id = int(raw)
    except ValueError:
        await message.answer("ID faqat raqam bo'lishi kerak. Qaytadan kiriting:")
        return
    try:
        await bot.send_message(chat_id, "✅ Bu kanal do'kon boti bilan ulandi.")
    except Exception:
        await message.answer(
            "⚠️ Botga bu kanalga xabar yubora olmadim. Botni kanalga admin qilib qo'shganingizga ishonch "
            "hosil qiling va ID ni qayta yuboring."
        )
        return
    with get_session() as db:
        set_setting(db, KEY_CHANNEL_ID, str(chat_id))
    await state.clear()
    await message.answer("✅ Kanal ulandi. Endi «📤 Kanalga yuborish» tugmasini qayta bosing.",
                          reply_markup=admin_main_menu())


# ---------- Karta ma'lumotlari ----------

@router.message(F.text == "💳 Karta sozlash", IsAdmin(), StateFilter(None))
async def start_card_setup(message: Message, state: FSMContext):
    await state.set_state(CardSetup.waiting_card_number)
    await message.answer("To'lov uchun karta raqamini kiriting:", reply_markup=cancel_keyboard())


@router.message(CardSetup.waiting_card_number)
async def save_card_number(message: Message, state: FSMContext):
    await state.update_data(card_number=message.text.strip())
    await state.set_state(CardSetup.waiting_card_owner)
    await message.answer("Karta egasining F.I.SH. sini kiriting:")


@router.message(CardSetup.waiting_card_owner)
async def save_card_owner(message: Message, state: FSMContext):
    data = await state.get_data()
    with get_session() as db:
        set_setting(db, KEY_CARD_NUMBER, data["card_number"])
        set_setting(db, KEY_CARD_OWNER, message.text.strip())
    await state.clear()
    await message.answer("✅ Karta ma'lumotlari saqlandi.", reply_markup=admin_main_menu())
