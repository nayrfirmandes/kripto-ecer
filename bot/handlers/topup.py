from decimal import Decimal
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma

from bot.formatters.messages import (
    format_topup_menu,
    format_topup_amount,
    format_topup_instruction,
    format_transaction_pending,
    format_error,
    Emoji,
)
from bot.keyboards.inline import (
    CallbackData,
    get_topup_methods_keyboard,
    get_topup_confirm_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
)
from bot.utils.helpers import parse_amount
from bot.db.queries import get_payment_methods, create_deposit
from bot.config import config

router = Router()

MIN_TOPUP = Decimal("10000")


class TopupStates(StatesGroup):
    selecting_method = State()
    entering_amount = State()
    confirming = State()


@router.callback_query(F.data == CallbackData.MENU_TOPUP)
async def show_topup_menu(callback: CallbackQuery, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user or user.status != "ACTIVE":
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    methods = await get_payment_methods(db)
    
    if not methods:
        await callback.message.edit_text(
            format_error("Belum ada metode pembayaran yang tersedia."),
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    method_list = [{"id": m.id, "type": m.type, "name": m.name} for m in methods]
    
    await state.set_state(TopupStates.selecting_method)
    
    await callback.message.edit_text(
        format_topup_menu(),
        reply_markup=get_topup_methods_keyboard(method_list),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("topup:method:") & ~F.data.endswith(":crypto"))
async def select_topup_method(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    method_id = callback.data.split(":")[-1]
    
    method = await db.paymentmethod.find_unique(where={"id": method_id})
    
    if not method:
        await callback.answer("Metode tidak ditemukan.", show_alert=True)
        return
    
    await state.update_data(
        method_id=method_id,
        method_name=method.name,
        method_type=method.type,
        account_no=method.accountNo,
        account_name=method.accountName,
    )
    await state.set_state(TopupStates.entering_amount)
    
    await callback.message.edit_text(
        format_topup_amount(method.name),
        reply_markup=get_cancel_keyboard(CallbackData.MENU_TOPUP),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(TopupStates.entering_amount)
async def process_topup_amount(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    amount = parse_amount(message.text)
    
    if not amount or amount < MIN_TOPUP:
        await message.answer(
            format_error(f"Jumlah minimal top up adalah Rp {MIN_TOPUP:,.0f}"),
            reply_markup=get_cancel_keyboard(CallbackData.MENU_TOPUP),
            parse_mode="HTML"
        )
        return
    
    if not user:
        await message.answer(format_error("User tidak ditemukan."), parse_mode="HTML")
        return
    
    data = await state.get_data()
    
    deposit = await create_deposit(
        db=db,
        user_id=user.id,
        amount=amount,
        payment_method=data["method_name"],
    )
    
    await state.update_data(deposit_id=deposit.id, amount=float(amount))
    await state.set_state(TopupStates.confirming)
    
    await message.answer(
        format_topup_instruction(
            method=data["method_name"],
            account_no=data.get("account_no", "-"),
            account_name=data.get("account_name", "-"),
            amount=amount,
        ),
        reply_markup=get_topup_confirm_keyboard(deposit.id),
        parse_mode="HTML"
    )
    
    for admin_id in config.bot.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"<b>Request Top Up Baru</b>\n\n"
                f"• User: {user.firstName or user.username} (ID: {user.telegramId})\n"
                f"• Jumlah: Rp {amount:,.0f}\n"
                f"• Via: {data['method_name']}\n\n"
                f"ID: <code>{deposit.id}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("topup:confirm:"))
async def confirm_topup(callback: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    
    await callback.message.edit_text(
        format_transaction_pending(),
        parse_mode="HTML"
    )
    await callback.answer("Terima kasih! Admin akan memproses top up Anda.", show_alert=True)


@router.callback_query(F.data.startswith("topup:cancel:"))
async def cancel_topup(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    deposit_id = callback.data.split(":")[-1]
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": "CANCELLED"}
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        "Top up dibatalkan.",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


