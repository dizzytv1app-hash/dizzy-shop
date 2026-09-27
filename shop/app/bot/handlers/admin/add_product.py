from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from app.database import get_session
from app.services.products import code_exists, create_product
from app.bot.utils.filters import IsAdmin
from app.bot.states import AddProduct
from app.bot.keyboards import cancel_keyboard, admin_main_menu

router = Router(name="add_product")


def finish_images_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Tugatish")], [KeyboardButton(text="🚫 Bekor qilish")]],
        resize_keyboard=True,
    )


@router.message(F.text == "➕ Kiyim qo'shish", IsAdmin(), StateFilter(None))
async def start_add_product(message: Message, state: FSMContext):
    await state.set_state(AddProduct.code)
    await message.answer(
        "🆕 Yangi mahsulot qo'shish.\n\n1️⃣ Mahsulot kodini kiriting (masalan: K001):",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddProduct.code, F.text == "🚫 Bekor qilish")
@router.message(AddProduct.name, F.text == "🚫 Bekor qilish")
@router.message(AddProduct.colors, F.text == "🚫 Bekor qilish")
@router.message(AddProduct.sizes, F.text == "🚫 Bekor qilish")
@router.message(AddProduct.price, F.text == "🚫 Bekor qilish")
@router.message(AddProduct.images, F.text == "🚫 Bekor qilish")
async def cancel_add_product(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(AddProduct.code)
async def process_code(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    if not code or len(code) > 15:
        await message.answer("Noto'g'ri kod. Qaytadan kiriting (masalan: K001):")
        return
    with get_session() as db:
        if code_exists(db, code):
            await message.answer(f"❗️ «{code}» kodi allaqachon mavjud. Boshqa kod kiriting:")
            return
    await state.update_data(code=code)
    await state.set_state(AddProduct.name)
    await message.answer("2️⃣ Kiyim nomini kiriting:")


@router.message(AddProduct.name)
async def process_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nom bo'sh bo'lmasin. Qaytadan kiriting:")
        return
    await state.update_data(name=name)
    await state.set_state(AddProduct.colors)
    await message.answer("3️⃣ Ranglarini vergul bilan ajratib kiriting (masalan: Qora, Oq, Ko'k):")


@router.message(AddProduct.colors)
async def process_colors(message: Message, state: FSMContext):
    colors = [c.strip() for c in (message.text or "").split(",") if c.strip()]
    if not colors:
        await message.answer("Kamida bitta rang kiriting:")
        return
    await state.update_data(colors=colors)
    await state.set_state(AddProduct.sizes)
    await message.answer("4️⃣ O'lchamlarini vergul bilan ajratib kiriting (masalan: S, M, L, XL):")


@router.message(AddProduct.sizes)
async def process_sizes(message: Message, state: FSMContext):
    sizes = [s.strip() for s in (message.text or "").split(",") if s.strip()]
    if not sizes:
        await message.answer("Kamida bitta o'lcham kiriting:")
        return
    await state.update_data(sizes=sizes)
    await state.set_state(AddProduct.price)
    await message.answer("5️⃣ Narxini so'mda kiriting (faqat raqam, masalan: 150000):")


@router.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    raw = (message.text or "").replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await message.answer("Narx faqat raqamlardan iborat bo'lsin (masalan: 150000):")
        return
    await state.update_data(price=int(raw), images=[])
    await state.set_state(AddProduct.images)
    await message.answer(
        "6️⃣ Kiyim rasmlarini yuboring (ko'pi bilan 3 ta: old tomoni, orqa tomoni, qo'shimcha ko'rinish).\n"
        "Kamida 1 ta rasm yuboring, so'ng «✅ Tugatish» tugmasini bosing.",
        reply_markup=finish_images_keyboard(),
    )


@router.message(AddProduct.images, F.photo)
async def process_image(message: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    if len(images) >= 3:
        await message.answer("Allaqachon 3 ta rasm yuborildi. «✅ Tugatish» tugmasini bosing.")
        return
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)
    if len(images) >= 3:
        await _finalize(message, state)
    else:
        await message.answer(f"✅ Rasm qabul qilindi ({len(images)}/3). Yana yuborishingiz "
                              f"yoki «✅ Tugatish» tugmasini bosishingiz mumkin.")


@router.message(AddProduct.images, F.text == "✅ Tugatish")
async def finish_images(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("images"):
        await message.answer("Kamida 1 ta rasm yuborishingiz kerak.")
        return
    await _finalize(message, state)


@router.message(AddProduct.images)
async def images_wrong_input(message: Message):
    await message.answer("Iltimos, rasm yuboring yoki «✅ Tugatish» tugmasini bosing.")


async def _finalize(message: Message, state: FSMContext):
    data = await state.get_data()
    with get_session() as db:
        product = create_product(
            db,
            code=data["code"],
            name=data["name"],
            price=data["price"],
            colors=data["colors"],
            sizes=data["sizes"],
            image_file_ids=data["images"],
        )
        code = product.code
    await state.clear()
    await message.answer(
        f"🎉 Mahsulot muvaffaqiyatli qo'shildi!\nKodi: <code>{code}</code>\n"
        f"Web-saytda avtomatik ko'rinadi.",
        reply_markup=admin_main_menu(),
    )
