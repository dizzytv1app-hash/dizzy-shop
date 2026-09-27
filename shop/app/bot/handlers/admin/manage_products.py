from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import get_session
from app.services.products import (
    get_product_by_code, update_field, replace_images, delete_product,
)
from app.bot.utils.filters import IsAdmin
from app.bot.states import ManageProduct
from app.bot.keyboards import (
    cancel_keyboard, admin_main_menu, manage_product_menu, confirm_delete_keyboard,
    color_manage_keyboard, size_manage_keyboard, finish_or_cancel_keyboard,
)
from app.bot.utils.formatting import product_card_text

router = Router(name="manage_products")


async def _show_product(message: Message, code: str):
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await message.answer(f"❗️ «{code}» kodli mahsulot topilmadi. Qaytadan kiriting:")
            return False
        text = product_card_text(product)
    await message.answer(text, reply_markup=manage_product_menu(code))
    return True


@router.message(F.text == "🛠 Kiyimlarni boshqarish", IsAdmin(), StateFilter(None))
async def start_manage(message: Message, state: FSMContext):
    await state.set_state(ManageProduct.waiting_code)
    await message.answer("Boshqarmoqchi bo'lgan mahsulot kodini kiriting:", reply_markup=cancel_keyboard())


@router.message(ManageProduct.waiting_code, F.text == "🚫 Bekor qilish")
async def cancel_manage(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.waiting_code)
async def receive_code(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    ok = await _show_product(message, code)
    if ok:
        await state.clear()


# ---------- Nomi ----------

@router.callback_query(F.data.startswith("editname:"), IsAdmin())
async def cb_edit_name(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    await state.update_data(code=code)
    await state.set_state(ManageProduct.edit_name)
    await callback.message.answer(f"«{code}» uchun yangi nom kiriting:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ManageProduct.edit_name, F.text == "🚫 Bekor qilish")
async def cancel_edit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.edit_name)
async def save_name(message: Message, state: FSMContext):
    data = await state.get_data()
    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return
        update_field(db, product, "name", message.text.strip())
    await state.clear()
    await message.answer("✅ Nom yangilandi.", reply_markup=admin_main_menu())


# ---------- Narxi ----------

@router.callback_query(F.data.startswith("editprice:"), IsAdmin())
async def cb_edit_price(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    await state.update_data(code=code)
    await state.set_state(ManageProduct.edit_price)
    await callback.message.answer(f"«{code}» uchun yangi narxni kiriting (so'mda):", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ManageProduct.edit_price, F.text == "🚫 Bekor qilish")
async def cancel_edit_price(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.edit_price)
async def save_price(message: Message, state: FSMContext):
    raw = (message.text or "").replace(" ", "")
    if not raw.isdigit():
        await message.answer("Narx faqat raqam bo'lsin:")
        return
    data = await state.get_data()
    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return
        # Narxni to'g'ridan-to'g'ri o'zgartirish chegirmani bekor qiladi (aniqlik uchun)
        product.old_price = None
        product.discount_percent = None
        update_field(db, product, "price", int(raw))
    await state.clear()
    await message.answer("✅ Narx yangilandi.", reply_markup=admin_main_menu())


# ---------- Ranglar / o'lchamlar (har birini alohida yoqib-o'chirish) ----------

@router.callback_query(F.data.startswith("editcolors:"), IsAdmin())
async def cb_edit_colors(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        colors = list(product.colors)
    await callback.message.edit_text(
        f"«{code}» ranglari. Bosilganda mavjud/mavjud emas holati almashadi:",
        reply_markup=color_manage_keyboard(code, colors),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_color:"), IsAdmin())
async def cb_toggle_color(callback: CallbackQuery):
    _, code, color_name = callback.data.split(":", 2)
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        color = next((c for c in product.colors if c.name == color_name), None)
        if color:
            color.is_available = not color.is_available
        colors = list(product.colors)
    await callback.message.edit_reply_markup(reply_markup=color_manage_keyboard(code, colors))
    await callback.answer()


@router.callback_query(F.data.startswith("add_color:"), IsAdmin())
async def cb_add_color_start(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    await state.update_data(code=code)
    await state.set_state(ManageProduct.edit_colors)
    await callback.message.answer(f"«{code}» uchun qo'shmoqchi bo'lgan yangi rang nomini kiriting:",
                                   reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ManageProduct.edit_colors, F.text == "🚫 Bekor qilish")
async def cancel_edit_colors(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.edit_colors)
async def save_new_color(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Rang nomini kiriting:")
        return
    data = await state.get_data()
    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return
        from app.models import ProductColor
        if any(c.name.lower() == name.lower() for c in product.colors):
            await message.answer("Bu rang allaqachon mavjud. Boshqa nom kiriting:")
            return
        db.add(ProductColor(product_id=product.id, name=name, is_available=True))
    await state.clear()
    await message.answer(f"✅ «{name}» rangi qo'shildi.", reply_markup=admin_main_menu())


@router.callback_query(F.data.startswith("editsizes:"), IsAdmin())
async def cb_edit_sizes(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        sizes = list(product.sizes)
    await callback.message.edit_text(
        f"«{code}» o'lchamlari. Bosilganda mavjud/mavjud emas holati almashadi:",
        reply_markup=size_manage_keyboard(code, sizes),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_size:"), IsAdmin())
async def cb_toggle_size(callback: CallbackQuery):
    _, code, size_name = callback.data.split(":", 2)
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        size = next((s for s in product.sizes if s.name == size_name), None)
        if size:
            size.is_available = not size.is_available
        sizes = list(product.sizes)
    await callback.message.edit_reply_markup(reply_markup=size_manage_keyboard(code, sizes))
    await callback.answer()


@router.callback_query(F.data.startswith("add_size:"), IsAdmin())
async def cb_add_size_start(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    await state.update_data(code=code)
    await state.set_state(ManageProduct.edit_sizes)
    await callback.message.answer(f"«{code}» uchun qo'shmoqchi bo'lgan yangi o'lcham nomini kiriting:",
                                   reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ManageProduct.edit_sizes, F.text == "🚫 Bekor qilish")
async def cancel_edit_sizes(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.edit_sizes)
async def save_new_size(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("O'lcham nomini kiriting:")
        return
    data = await state.get_data()
    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return
        from app.models import ProductSize
        if any(s.name.lower() == name.lower() for s in product.sizes):
            await message.answer("Bu o'lcham allaqachon mavjud. Boshqa nom kiriting:")
            return
        db.add(ProductSize(product_id=product.id, name=name, is_available=True))
    await state.clear()
    await message.answer(f"✅ «{name}» o'lchami qo'shildi.", reply_markup=admin_main_menu())


@router.callback_query(F.data.startswith("back_to_product:"), IsAdmin())
async def cb_back_to_product(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    with get_session() as db:
        product = get_product_by_code(db, code)
        if not product:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        text = product_card_text(product)
    await callback.message.edit_text(text, reply_markup=manage_product_menu(code))
    await callback.answer()


# ---------- Rasmlar ----------

@router.callback_query(F.data.startswith("editimages:"), IsAdmin())
async def cb_edit_images(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    await state.update_data(code=code, images=[])
    await state.set_state(ManageProduct.edit_images)
    await callback.message.answer(
        f"«{code}» uchun yangi rasmlarni yuboring (ko'pi bilan 3 ta), so'ng «✅ Tugatish» tugmasini bosing.",
        reply_markup=finish_or_cancel_keyboard(),
    )
    await callback.answer()


@router.message(ManageProduct.edit_images, F.text == "🚫 Bekor qilish")
async def cancel_edit_images(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(ManageProduct.edit_images, F.photo)
async def collect_new_images(message: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    if len(images) >= 3:
        await message.answer("Allaqachon 3 ta rasm qabul qilindi. «✅ Tugatish» deb yozing.")
        return
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)
    await message.answer(f"✅ Qabul qilindi ({len(images)}/3).")


@router.message(ManageProduct.edit_images, F.text == "✅ Tugatish")
async def finish_new_images(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("images"):
        await message.answer("Kamida 1 ta rasm yuboring.")
        return
    with get_session() as db:
        product = get_product_by_code(db, data["code"])
        if not product:
            await state.clear()
            await message.answer("Mahsulot topilmadi.", reply_markup=admin_main_menu())
            return
        replace_images(db, product, data["images"])
    await state.clear()
    await message.answer("✅ Rasmlar yangilandi.", reply_markup=admin_main_menu())


# ---------- O'chirish ----------

@router.callback_query(F.data.startswith("delprod:"), IsAdmin())
async def cb_delete_ask(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    await callback.message.answer(
        f"«{code}» mahsulotini o'chirishga ishonchingiz komilmi?", reply_markup=confirm_delete_keyboard(code)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delprod_yes:"), IsAdmin())
async def cb_delete_confirm(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    with get_session() as db:
        product = get_product_by_code(db, code)
        if product:
            delete_product(db, product)
    await callback.message.answer(f"🗑 «{code}» mahsuloti o'chirildi (endi saytda ko'rinmaydi).")
    await callback.answer()


@router.callback_query(F.data == "delprod_no", IsAdmin())
async def cb_delete_cancel(callback: CallbackQuery):
    await callback.message.answer("Bekor qilindi.")
    await callback.answer()
