from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    code = State()
    name = State()
    colors = State()
    sizes = State()
    price = State()
    images = State()


class ManageProduct(StatesGroup):
    waiting_code = State()
    menu = State()
    edit_name = State()
    edit_price = State()
    edit_colors = State()
    edit_sizes = State()
    edit_images = State()
    confirm_delete = State()


class Discount(StatesGroup):
    waiting_code = State()
    waiting_new_price = State()


class AdminManage(StatesGroup):
    waiting_new_admin_id = State()
    waiting_remove_admin_id = State()


class HelpChatSetup(StatesGroup):
    waiting_chat_id = State()


class ChannelSetup(StatesGroup):
    waiting_channel_id = State()


class CardSetup(StatesGroup):
    waiting_card_number = State()
    waiting_card_owner = State()


class SendToChannel(StatesGroup):
    waiting_code = State()


class HelpRequestFlow(StatesGroup):
    waiting_message = State()


class UserOrderFlow(StatesGroup):
    choosing_color = State()
    choosing_size = State()
    confirm = State()


class PaymentFlow(StatesGroup):
    waiting_receipt = State()
