from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database import get_session
from app.services.products import get_product_by_code, set_discount, remove_discount
from app.bot.utils.filters import IsAdmin
from app.bot.utils.formatting import fmt_price
from app.bot.keyboards import cancel_keyboard, admin_main_menu
from app.bot.states import Discount

router = Router(name="discounts")


@router.message(F.text == "🏷 Chegirmalar", IsAdmin(), StateFilter(None))
async def start_discount(message: Message, state: FSMContext):
    await state.set_state(Discount.waiting_code)
    await message.answer(
        "Chegirma qo'ymoqchi bo'lgan mahsulot kodini kiriting.\n"
        "(Chegirmani bekor qilish uchun kodni kiritib, keyin «0» deb yozing.)",
        reply_markup=cancel_keyboard(),
    )


@router.message(Discount.waiting_code, F.text == "🚫 Bekor qilish")
@router.message(Discount.waiting_new_price, F.text == "🚫 Bekor qilish")
async def cancel_discount(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(Discount.waiting_code)
async def receive_discount_code(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await message.answer(f"❗️ «{code}» kodli mahsulot topilmadi. Qaytadan kiriting:")
            return
        current_price = product.price

    await state.update_data(code=code, current_price=current_price)
    await state.set_state(Discount.waiting_new_price)
    await message.answer(
        f"Hozirgi narx: {fmt_price(current_price)}\n\n"
        f"Yangi (chegirmali) narxni kiriting. Chegirmani olib tashlash uchun «0» deb yozing:"
    )


@router.message(Discount.waiting_new_price)
async def receive_new_price(message: Message, state: FSMContext):
    raw = (message.text or "").replace(" ", "")
    if not raw.isdigit():
        await message.answer("Narx faqat raqam bo'lsin:")
        return

    data = await state.get_data()
    new_price = int(raw)

    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return

        if new_price == 0:
            remove_discount(db, product)
            await state.clear()
            await message.answer("✅ Chegirma olib tashlandi, narx odatdagidek ko'rsatiladi.",
                                  reply_markup=admin_main_menu())
            return

        if new_price >= data["current_price"]:
            await message.answer(
                f"Yangi narx hozirgi narxdan ({fmt_price(data['current_price'])}) kichik bo'lishi kerak. "
                f"Qaytadan kiriting:"
            )
            return

        percent = set_discount(db, product, new_price)

    await state.clear()
    await message.answer(
        f"🏷 Chegirma qo'yildi!\n"
        f"Eski narx: <s>{fmt_price(data['current_price'])}</s>\n"
        f"Yangi narx: <b>{fmt_price(new_price)}</b>\n"
        f"Chegirma: <b>{percent}%</b>",
        reply_markup=admin_main_menu(),
    )
