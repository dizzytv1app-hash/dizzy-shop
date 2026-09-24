from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.config import settings
from app.states import ContentEdit
from app.keyboards import admin_menu_keyboard, back_to_menu_keyboard, content_menu_keyboard
from app.api_client import get_stats, get_content, update_content, ApiError

router = Router(name="admin")

CONTENT_LABELS = {
    "onboarding": "🆕 Birinchi ochilish matni",
    "guide": "📖 Qo'llanma matni",
    "shop_info": "🏬 Do'kon haqida",
}


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Ruxsat yo'q. Bu bo'lim faqat adminlar uchun.")
        return
    await message.answer("🔑 Admin panel", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "adm:menu")
async def cb_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("🔑 Admin panel", reply_markup=admin_menu_keyboard())
    await call.answer()


@router.callback_query(F.data == "adm:cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("Bekor qilindi. 🔑 Admin panel", reply_markup=admin_menu_keyboard())
    await call.answer()


@router.callback_query(F.data == "adm:stats")
async def cb_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await call.answer()
    try:
        s = await get_stats(call.from_user.id)
    except ApiError as e:
        await call.message.edit_text(f"Xato: {e.detail}", reply_markup=back_to_menu_keyboard())
        return

    text = (
        "📊 Statistika\n\n"
        f"👥 Foydalanuvchilar: {s['total_users']}\n"
        f"📦 Mahsulotlar: {s['total_products']}\n"
        f"🛒 Buyurtmalar: {s['total_orders']}\n"
        f"💰 Umumiy savdo: {int(s['total_sales'])} so'm\n\n"
        f"📅 Bugungi buyurtmalar: {s['today_orders']}\n"
        f"💰 Bugungi savdo: {int(s['today_sales'])} so'm\n"
        f"📈 Haftalik savdo: {int(s['weekly_sales'])} so'm\n"
        f"📈 Oylik savdo: {int(s['monthly_sales'])} so'm\n\n"
        f"💬 Yordam so'rovlari: {s['total_help_requests']} (yangi: {s['new_help_requests']})\n"
    )
    if s["best_sellers"]:
        text += "\n🔥 Eng ko'p sotilganlar:\n" + "\n".join(
            f"{i}. {p['name']} — {p['sold']} dona" for i, p in enumerate(s["best_sellers"], 1)
        )
    if s["low_stock"]:
        text += "\n\n⚠️ Kam qolgan mahsulotlar:\n" + "\n".join(
            f"• {p['name']} — {p['stock']} dona qoldi" for p in s["low_stock"]
        )

    await call.message.edit_text(text, reply_markup=back_to_menu_keyboard())


@router.callback_query(F.data == "adm:settings")
async def cb_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await call.answer()
    text = (
        "⚙️ Sozlamalar\n\n"
        f"🏬 Do'kon: {settings.SHOP_NAME}\n"
        f"🌐 Mini App: {settings.WEBAPP_URL}\n"
        f"🔗 Backend API: {settings.API_BASE_URL}\n"
        f"👤 Adminlar soni: {len(settings.ADMIN_IDS)}\n\n"
        "O'zgartirish uchun bot serveridagi .env faylini tahrirlang."
    )
    await call.message.edit_text(text, reply_markup=back_to_menu_keyboard())


# ---------- Ilova ma'lumoti (onboarding / guide / shop_info) ----------

@router.callback_query(F.data == "adm:content")
async def cb_content_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await call.answer()
    await call.message.edit_text(
        "📢 Ilova ma'lumoti\n\nMini appda ko'rinadigan matnlarni shu yerdan tahrirlaysiz:",
        reply_markup=content_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("adm:content_edit:"))
async def cb_content_edit_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    key = call.data.split(":")[2]
    await call.answer()
    try:
        current = await get_content(key)
    except ApiError as e:
        await call.message.edit_text(f"Xato: {e.detail}", reply_markup=back_to_menu_keyboard())
        return

    await state.set_state(ContentEdit.waiting_text)
    await state.update_data(key=key)
    await call.message.answer(
        f"{CONTENT_LABELS.get(key, key)}\n\nHozirgi matn:\n\n{current['value']}\n\n"
        "Yangi matnni yuboring (butun matnni almashtiradi):"
    )


@router.message(ContentEdit.waiting_text)
async def content_edit_save(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["key"]
    try:
        await update_content(message.from_user.id, key, message.text)
        await message.answer(f"✅ {CONTENT_LABELS.get(key, key)} yangilandi — mini appda darhol ko'rinadi.")
    except ApiError as e:
        await message.answer(f"❌ Xato: {e.detail}")
    await state.clear()
