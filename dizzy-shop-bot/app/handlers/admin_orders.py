from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.handlers.admin import is_admin
from app.keyboards import order_status_keyboard, pagination_keyboard, back_to_menu_keyboard
from app.api_client import list_orders, set_order_status, ApiError

router = Router(name="admin_orders")

STATUS_LABELS = {"new": "🆕 Yangi", "processing": "⏳ Jarayonda", "completed": "✅ Bajarildi", "cancelled": "🚫 Bekor qilindi"}


@router.callback_query(F.data.startswith("adm:orders:"))
async def cb_orders_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    page = int(call.data.split(":")[2])
    await call.answer()
    try:
        data = await list_orders(call.from_user.id, page=page)
    except ApiError as e:
        await call.message.edit_text(f"Xato: {e.detail}", reply_markup=back_to_menu_keyboard())
        return

    items = data.get("items", [])
    if not items:
        await call.message.edit_text("🛒 Hozircha buyurtma yo'q.", reply_markup=back_to_menu_keyboard())
        return

    await call.message.edit_text(
        f"🛒 Buyurtmalar (sahifa {page + 1})",
        reply_markup=pagination_keyboard("adm:orders", page, data.get("has_next", False)),
    )
    for o in items:
        text = (
            f"🆔 Buyurtma #{o['id']}\n👤 {o.get('customer', 'Mehmon')}\n"
            f"💵 {int(o['total_price'])} so'm | {STATUS_LABELS.get(o['status'], o['status'])}\n"
            f"📅 {o.get('created_at', '')}"
        )
        await call.message.answer(text, reply_markup=order_status_keyboard(o["id"]))


@router.callback_query(F.data.startswith("adm:order_status:"))
async def cb_set_status(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    _, _, order_id, status = call.data.split(":")
    try:
        await set_order_status(call.from_user.id, int(order_id), status)
        await call.answer(f"Holat yangilandi: {STATUS_LABELS.get(status, status)}")
        await call.message.edit_text(call.message.text + f"\n\n➡️ Yangi holat: {STATUS_LABELS.get(status, status)}")
    except ApiError as e:
        await call.answer(f"Xato: {e.detail}", show_alert=True)
