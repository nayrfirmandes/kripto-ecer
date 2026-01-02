from decimal import Decimal
from typing import Optional, Any
from aiogram import Router, F
from aiogram.types import CallbackQuery
from prisma import Prisma
from prisma.models import User

from bot.formatters.messages import format_balance
from bot.keyboards.inline import CallbackData, get_balance_keyboard
from bot.utils.telegram_helpers import safe_edit_text

router = Router()


@router.callback_query(F.data == CallbackData.MENU_BALANCE)
async def show_balance(
    callback: CallbackQuery,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    
    await safe_edit_text(
        callback,
        format_balance(balance),
        reply_markup=get_balance_keyboard()
    )
    await callback.answer()
