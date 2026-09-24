from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.handlers.admin import is_admin
from app.states import SupportReply
from app.keyboards import support_status_keyboard, pagination_keyboard, back_to_menu_keyboard
from app.api_client import list_support_tickets, reply_support_ticket, ApiError

router = Router(name="admin_support")

STATUS_LABELS = {"new": "🆕 Yangi", "in_progress": "⏳ Jarayonda", "resolved": "✅ Hal qilindi"}


@router.callback_query(F.data.startswith("adm:support:"))
async def cb_support_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    page = int(call.data.split(":")[2])
    await call.answer()
    try:
        data = await list_support_tickets(call.from_user.id, page=page)
    except ApiError as e:
        await call.message.edit_text(f"Xato: {e.detail}", reply_markup=back_to_menu_keyboard())
        return

    items = data.get("items", [])
    if not items:
        await call.message.edit_text("💬 Hozircha yordam so'rovi yo'q.", reply_markup=back_to_menu_keyboard())
        return

    await call.message.edit_text(
        f"💬 Yordam so'rovlari (sahifa {page + 1})",
        reply_markup=pagination_keyboard("adm:support", page, data.get("has_next", False)),
    )
    for t in items:
        status = STATUS_LABELS.get(t.get("status"), t.get("status"))
        text = (
            f"🆔 #{t['id']} — {t.get('username') or 'Foydalanuvchi'} (ID: {t['user_id']})\n"
            f"Holat: {status}\n📅 {t.get('created_at', '')}\n\n{t.get('message', '')}"
        )
        if t.get("photo_file_id"):
            await call.message.answer_photo(t["photo_file_id"], caption=text, reply_markup=support_status_keyboard(t["id"]))
        else:
            await call.message.answer(text, reply_markup=support_status_keyboard(t["id"]))


@router.callback_query(F.data.startswith("adm:help_status:"))
async def cb_set_help_status(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    _, _, ticket_id, status = call.data.split(":")
    try:
        await reply_support_ticket(call.from_user.id, int(ticket_id), status=status)
        await call.answer(f"Holat: {STATUS_LABELS.get(status, status)}")
    except ApiError as e:
        await call.answer(f"Xato: {e.detail}", show_alert=True)


@router.callback_query(F.data.startswith("adm:reply:"))
async def start_reply(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    ticket_id = int(call.data.split(":")[2])
    await state.set_state(SupportReply.waiting_reply)
    await state.update_data(ticket_id=ticket_id)
    await call.answer()
    await call.message.answer(f"✍️ #{ticket_id} uchun javobingizni yozing:")


@router.message(SupportReply.waiting_reply)
async def send_reply(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    ticket_id = data["ticket_id"]
    try:
        result = await reply_support_ticket(message.from_user.id, ticket_id, reply=message.text)
        user_id = result.get("user_id")
        if user_id:
            try:
                await bot.send_message(user_id, f"💬 Admin javobi:\n\n{message.text}")
            except Exception:
                pass
        await message.answer(f"✅ #{ticket_id} ga javob yuborildi va \"hal qilindi\" deb belgilandi.")
    except ApiError as e:
        await message.answer(f"❌ Xato: {e.detail}")
    await state.clear()
