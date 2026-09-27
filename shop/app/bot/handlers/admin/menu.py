from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.utils.filters import IsAdmin
from app.bot.keyboards import admin_main_menu, main_user_keyboard

router = Router(name="admin_menu")


@router.message(Command("admin"), IsAdmin())
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔐 Admin paneli. Kerakli bo'limni tanlang:", reply_markup=admin_main_menu())


@router.message(F.text == "⬅️ Chiqish", IsAdmin())
async def admin_exit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Admin panelidan chiqdingiz.", reply_markup=main_user_keyboard())
