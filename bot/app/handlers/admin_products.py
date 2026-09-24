from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.handlers.admin import is_admin
from app.states import AddProduct, EditProduct, ProductSearch
from app.keyboards import confirm_cancel_keyboard, back_to_menu_keyboard, product_row_keyboard, pagination_keyboard
from app.api_client import create_product, update_product, delete_product, list_products, ApiError

router = Router(name="admin_products")

FIELD_LABELS = {"name": "Nomi", "price": "Narxi", "sizes": "O'lchamlari", "colors": "Ranglari", "stock": "Qoldig'i", "photo": "Rasmi"}


# ---------- Ro'yxat / qidiruv ----------

async def _render_page(message_or_call, admin_id: int, page: int, search: str | None, edit: bool):
    try:
        data = await list_products(admin_id, page=page, search=search)
    except ApiError as e:
        text = f"Xato: {e.detail}"
        if edit:
            await message_or_call.message.edit_text(text, reply_markup=back_to_menu_keyboard())
        else:
            await message_or_call.answer(text, reply_markup=back_to_menu_keyboard())
        return

    items = data.get("items", [])
    if not items:
        text = "📦 Mahsulot topilmadi." if search else "📦 Hozircha mahsulot yo'q."
        if edit:
            await message_or_call.message.edit_text(text, reply_markup=back_to_menu_keyboard())
        else:
            await message_or_call.answer(text, reply_markup=back_to_menu_keyboard())
        return

    header = f"📦 Mahsulotlar (sahifa {page + 1})" + (f" — qidiruv: {search}" if search else "")
    kb = pagination_keyboard("adm:products", page, data.get("has_next", False))
    if edit:
        await message_or_call.message.edit_text(header, reply_markup=kb)
        target = message_or_call.message
    else:
        await message_or_call.answer(header, reply_markup=kb)
        target = message_or_call

    for p in items:
        text = f"🆔 {p['id']} — {p['name']}\n💵 {int(p['price'])} so'm | 📦 {p['stock']} dona"
        await target.answer(text, reply_markup=product_row_keyboard(p["id"]))


@router.callback_query(F.data.startswith("adm:products:"))
async def cb_products_list(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    page = int(call.data.split(":")[2])
    await call.answer()
    await _render_page(call, call.from_user.id, page, search=None, edit=True)


@router.callback_query(F.data.startswith("adm:delete:"))
async def cb_delete_product(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    product_id = int(call.data.split(":")[2])
    try:
        await delete_product(call.from_user.id, product_id)
        await call.answer("O'chirildi ✅")
        await call.message.edit_text(f"🗑 Mahsulot #{product_id} o'chirildi.")
    except ApiError as e:
        await call.answer(f"Xato: {e.detail}", show_alert=True)


# ---------- Tahrirlash (bitta maydon) ----------

@router.callback_query(F.data.startswith("adm:editf:"))
async def cb_edit_field(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    _, _, product_id, field = call.data.split(":")
    await state.set_state(EditProduct.waiting_field_value)
    await state.update_data(product_id=int(product_id), field=field)
    await call.answer()

    if field == "photo":
        await call.message.answer(f"🖼 Mahsulot #{product_id} uchun yangi rasm yuboring:")
    elif field in ("sizes", "colors"):
        await call.message.answer(f"{FIELD_LABELS[field]} uchun yangi qiymatlarni vergul bilan yozing (masalan: S, M, L):")
    else:
        await call.message.answer(f"{FIELD_LABELS[field]} uchun yangi qiymatni yozing:")


@router.message(EditProduct.waiting_field_value, F.photo)
async def edit_field_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data["field"] != "photo":
        await message.answer("❗️ Bu maydon uchun rasm emas, matn kutilmoqda.")
        return
    await _apply_edit(message, data["product_id"], {"image_file_id": message.photo[-1].file_id})
    await state.clear()


@router.message(EditProduct.waiting_field_value, F.text)
async def edit_field_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field, product_id = data["field"], data["product_id"]

    if field == "photo":
        await message.answer("❗️ Iltimos, rasm yuboring.")
        return
    if field == "price":
        raw = message.text.strip().replace(" ", "")
        if not raw.isdigit():
            await message.answer("❗️ Narx faqat raqam bo'lishi kerak:")
            return
        payload = {"price": int(raw)}
    elif field == "stock":
        raw = message.text.strip()
        if not raw.isdigit():
            await message.answer("❗️ Qoldiq faqat raqam bo'lishi kerak:")
            return
        payload = {"stock": int(raw)}
    elif field in ("sizes", "colors"):
        payload = {field: [v.strip() for v in message.text.split(",") if v.strip()]}
    else:  # name
        payload = {"name": message.text.strip()}

    await _apply_edit(message, product_id, payload)
    await state.clear()


async def _apply_edit(message: Message, product_id: int, payload: dict):
    try:
        await update_product(message.from_user.id, product_id, payload)
        await message.answer(f"✅ Mahsulot #{product_id} yangilandi — mini appda ko'rinadi.")
    except ApiError as e:
        await message.answer(f"❌ Xato: {e.detail}")


# ---------- Qo'shish (FSM): rasm -> nom -> narx -> o'lcham -> rang -> qoldiq ----------

@router.callback_query(F.data == "adm:add_product")
async def start_add_product(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await state.set_state(AddProduct.photo)
    await call.answer()
    await call.message.edit_text("➕ Yangi mahsulot\n\n1️⃣ Mahsulot rasmini yuboring:")


@router.message(AddProduct.photo, F.photo)
async def add_photo(message: Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(AddProduct.name)
    await message.answer("2️⃣ Mahsulot nomini yozing:")


@router.message(AddProduct.photo)
async def add_photo_invalid(message: Message):
    await message.answer("❗️ Iltimos, rasm yuboring (matn emas).")


@router.message(AddProduct.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.price)
    await message.answer("3️⃣ Narxini kiriting (so'mda, faqat raqam):")


@router.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "")
    if not raw.isdigit():
        await message.answer("❗️ Narx faqat raqam bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(price=int(raw))
    await state.set_state(AddProduct.sizes)
    await message.answer("4️⃣ Mavjud o'lchamlarni vergul bilan yozing (masalan: S, M, L, XL):")


@router.message(AddProduct.sizes)
async def add_sizes(message: Message, state: FSMContext):
    sizes = [s.strip() for s in message.text.split(",") if s.strip()]
    await state.update_data(sizes=sizes)
    await state.set_state(AddProduct.colors)
    await message.answer("5️⃣ Mavjud ranglarni vergul bilan yozing (masalan: Qora, Oq, Kulrang):")


@router.message(AddProduct.colors)
async def add_colors(message: Message, state: FSMContext):
    colors = [c.strip() for c in message.text.split(",") if c.strip()]
    await state.update_data(colors=colors)
    await state.set_state(AddProduct.stock)
    await message.answer("6️⃣ Ombordagi umumiy miqdorini kiriting (dona):")


@router.message(AddProduct.stock)
async def add_stock(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("❗️ Miqdor faqat raqam bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(stock=int(raw))
    data = await state.get_data()
    await state.set_state(AddProduct.confirm)

    summary = (
        "📋 Tekshiring:\n\n"
        f"Nomi: {data['name']}\n"
        f"Narxi: {data['price']} so'm\n"
        f"O'lchamlar: {', '.join(data['sizes'])}\n"
        f"Ranglar: {', '.join(data['colors'])}\n"
        f"Qoldiq: {data['stock']} dona\n"
    )
    await message.answer_photo(data["photo_file_id"], caption=summary, reply_markup=confirm_cancel_keyboard("adm:save_product"))


@router.callback_query(AddProduct.confirm, F.data == "adm:save_product")
async def save_product(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    payload = {
        "name": data["name"], "price": data["price"], "sizes": data["sizes"],
        "colors": data["colors"], "stock": data["stock"], "image_file_id": data["photo_file_id"],
    }
    try:
        await create_product(call.from_user.id, payload)
        await call.message.edit_caption(caption=(call.message.caption or "") + "\n\n✅ Saqlandi — mini appda endi ko'rinadi.")
    except ApiError as e:
        await call.message.edit_caption(caption=(call.message.caption or "") + f"\n\n❌ Xato: {e.detail}")
    await state.clear()


# ---------- Qidiruv (mahsulotlar bo'limidan) ----------

@router.message(ProductSearch.waiting_query)
async def search_products(message: Message, state: FSMContext):
    await state.clear()
    await _render_page(message, message.from_user.id, page=0, search=message.text.strip(), edit=False)
