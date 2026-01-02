from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery
from prisma import Prisma

from bot.formatters.messages import format_balance
from bot.keyboards.inline import CallbackData, get_balance_keyboard

router = Router()


@router.callback_query(F.data == CallbackData.MENU_BALANCE)
async def show_balance(callback: CallbackQuery, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else 0
    
    await callback.message.edit_text(
        format_balance(balance),
        reply_markup=get_balance_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
