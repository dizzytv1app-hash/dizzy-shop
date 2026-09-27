from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.database import get_session
from app.services.users import add_admin, remove_admin, list_admins, is_owner
from app.bot.utils.filters import IsAdmin, IsOwner
from app.bot.keyboards import cancel_keyboard, admin_main_menu
from app.bot.states import AdminManage

router = Router(name="admins")


def admins_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="admin_remove")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="admin_list")],
    ])


@router.message(F.text == "👤 Adminlar", IsAdmin(), StateFilter(None))
async def open_admins(message: Message):
    await message.answer("👤 Adminlar bo'limi:", reply_markup=admins_menu())


@router.callback_query(F.data == "admin_list", IsAdmin())
async def cb_list(callback):
    with get_session() as db:
        admins = list_admins(db)
    lines = ["👤 Adminlar ro'yxati:\n"]
    for a in admins:
        role = "👑 Bot egasi" if a.is_owner else "🔧 Admin"
        uname = f"@{a.username}" if a.username else ""
        lines.append(f"{role} — <code>{a.telegram_id}</code> {uname}")
    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "admin_add", IsOwner())
async def cb_add_start(callback, state: FSMContext):
    await state.set_state(AdminManage.waiting_new_admin_id)
    await callback.message.answer("Yangi admin qilmoqchi bo'lgan foydalanuvchining Telegram ID raqamini kiriting:",
                                   reply_markup=cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def cb_add_denied(callback):
    await callback.answer("Faqat bot egasi yangi admin qo'sha oladi.", show_alert=True)


@router.message(AdminManage.waiting_new_admin_id, F.text == "🚫 Bekor qilish")
@router.message(AdminManage.waiting_remove_admin_id, F.text == "🚫 Bekor qilish")
async def cancel_admin_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(AdminManage.waiting_new_admin_id)
async def receive_new_admin_id(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Telegram ID faqat raqamlardan iborat bo'ladi. Qaytadan kiriting:")
        return
    tg_id = int(raw)
    with get_session() as db:
        ok, msg = add_admin(db, tg_id, None, message.from_user.id)
    await state.clear()
    await message.answer(("✅ " if ok else "❗️ ") + msg, reply_markup=admin_main_menu())


@router.callback_query(F.data == "admin_remove", IsOwner())
async def cb_remove_start(callback, state: FSMContext):
    await state.set_state(AdminManage.waiting_remove_admin_id)
    await callback.message.answer("O'chirmoqchi bo'lgan adminning Telegram ID raqamini kiriting:",
                                   reply_markup=cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_remove")
async def cb_remove_denied(callback):
    await callback.answer("Faqat bot egasi admin o'chira oladi.", show_alert=True)


@router.message(AdminManage.waiting_remove_admin_id)
async def receive_remove_admin_id(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Telegram ID faqat raqamlardan iborat bo'ladi. Qaytadan kiriting:")
        return
    tg_id = int(raw)
    with get_session() as db:
        ok, msg = remove_admin(db, tg_id, message.from_user.id)
    await state.clear()
    await message.answer(("✅ " if ok else "❗️ ") + msg, reply_markup=admin_main_menu())
