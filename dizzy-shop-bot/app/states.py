from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    photo = State()
    name = State()
    price = State()
    sizes = State()
    colors = State()
    stock = State()
    confirm = State()


class EditProduct(StatesGroup):
    waiting_field_value = State()


class AddDiscount(StatesGroup):
    target_type = State()
    target_value = State()
    percent = State()


class HelpForm(StatesGroup):
    waiting_message = State()


class SupportReply(StatesGroup):
    waiting_reply = State()


class ContentEdit(StatesGroup):
    waiting_text = State()


class ProductSearch(StatesGroup):
    waiting_query = State()
