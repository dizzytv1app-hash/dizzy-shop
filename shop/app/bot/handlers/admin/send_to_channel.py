from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto

from app.database import get_session
from app.services.products import get_product_by_code
from app.services.settings_service import get_setting, KEY_CHANNEL_ID
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import product_card_text
from app.bot.keyboards import admin_main_menu, channel_order_button, cancel_keyboard
from app.bot.states import SendToChannel

router = Router(name="send_to_channel")


@router.message(SendToChannel.waiting_code, F.text == "🚫 Bekor qilish")
async def cancel_send(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(SendToChannel.waiting_code)
async def send_product_to_channel(message: Message, state: FSMContext, bot):
    code = (message.text or "").strip().upper()
    with get_session() as db:
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            await message.answer(f"❗️ «{code}» kodli faol mahsulot topilmadi. Qaytadan kiriting:")
            return
        channel_id = get_setting(db, KEY_CHANNEL_ID)
        text = product_card_text(product)
        images = [img.file_id for img in product.images]

    if not channel_id:
        await state.clear()
        await message.answer("❗️ Kanal ulanmagan. Avval «📤 Kanalga yuborish» orqali kanalni ulang.",
                              reply_markup=admin_main_menu())
        return

    try:
        me = await bot.get_me()
        markup = channel_order_button(code, me.username)
        if not images:
            await bot.send_message(int(channel_id), text, reply_markup=markup)
        elif len(images) == 1:
            await bot.send_photo(int(channel_id), images[0], caption=text, reply_markup=markup)
        else:
            media = [InputMediaPhoto(media=fid, caption=text if i == 0 else None)
                     for i, fid in enumerate(images)]
            sent = await bot.send_media_group(int(channel_id), media)
            # Media-group'ga inline tugma biriktirib bo'lmaydi, shu uchun alohida xabar bilan tugma yuboramiz
            await bot.send_message(int(channel_id), f"👆 {product.name} ({code})", reply_markup=markup)
    except Exception:
        await state.clear()
        await message.answer("⚠️ Kanalga yubora olmadim. Bot kanalda admin ekanini tekshiring.",
                              reply_markup=admin_main_menu())
        return

    await state.clear()
    await message.answer("✅ Mahsulot kanalga yuborildi.", reply_markup=admin_main_menu())
