from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import get_session
from app.services.products import get_product_by_code, sold_count
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import fmt_price
from app.bot.keyboards import cancel_keyboard, admin_main_menu
from aiogram.fsm.state import State, StatesGroup


class Analyze(StatesGroup):
    waiting_code = State()


router = Router(name="analyze")


@router.message(F.text == "📊 Kiyimlarni tahlillash", IsAdmin(), StateFilter(None))
async def start_analyze(message: Message, state: FSMContext):
    await state.set_state(Analyze.waiting_code)
    await message.answer("Tahlil qilmoqchi bo'lgan mahsulot kodini kiriting:", reply_markup=cancel_keyboard())


@router.message(Analyze.waiting_code, F.text == "🚫 Bekor qilish")
async def cancel_analyze(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(Analyze.waiting_code)
async def show_analysis(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await message.answer(f"❗️ «{code}» kodli mahsulot topilmadi. Qaytadan kiriting:")
            return
        count = sold_count(db, product.id)
        revenue = count * product.price

    await state.clear()
    text = (
        f"📊 <b>{product.name}</b> ({product.code})\n\n"
        f"Sotilgan (to'lovi tasdiqlangan) buyurtmalar: <b>{count}</b> ta\n"
        f"Ushbu mahsulotdan tushgan taxminiy tushum: <b>{fmt_price(revenue)}</b>"
    )
    await message.answer(text, reply_markup=admin_main_menu())
