from typing import Optional
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup

from bot.config import config


class AdminStates(StatesGroup):
    editing_buy_margin = State()
    editing_sell_margin = State()
    editing_min_buy = State()
    editing_max_buy = State()
    editing_min_sell = State()
    editing_max_sell = State()
    adding_payment_name = State()
    adding_payment_type = State()
    adding_payment_account_no = State()
    adding_payment_account_name = State()
    editing_referrer_bonus = State()
    editing_referee_bonus = State()


def is_admin(user_id: Optional[int]) -> bool:
    if user_id is None:
        return False
    return user_id in config.bot.admin_ids


async def safe_edit_text(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> None:
    from aiogram.types import Message as AiogramMessage
    msg = callback.message
    if msg is not None and isinstance(msg, AiogramMessage):
        try:
            await msg.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception:
            pass
