from decimal import Decimal
from typing import Optional, Any
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma
from prisma.models import User

from bot.formatters.messages import (
    format_withdraw_menu,
    format_transaction_pending,
    format_error,
    format_insufficient_balance,
    Emoji,
)
from bot.keyboards.inline import (
    CallbackData,
    get_withdraw_methods_keyboard,
    get_ewallet_options_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_confirm_keyboard,
)
from bot.utils.helpers import parse_amount
from bot.utils.telegram_helpers import safe_edit_text, get_callback_data
from bot.db.queries import create_withdrawal
from bot.config import config

router = Router()

MIN_WITHDRAW = Decimal("50000")


class WithdrawStates(StatesGroup):
    selecting_method = State()
    entering_bank_name = State()
    entering_account_number = State()
    entering_account_name = State()
    entering_ewallet_number = State()
    entering_amount = State()
    confirming = State()


@router.callback_query(F.data == CallbackData.MENU_WITHDRAW)
async def show_withdraw_menu(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    if not user or user.status != "ACTIVE":
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    
    if balance < MIN_WITHDRAW:
        await safe_edit_text(
            callback,
            format_insufficient_balance(MIN_WITHDRAW, balance),
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(WithdrawStates.selecting_method)
    
    await safe_edit_text(
        callback,
        format_withdraw_menu(),
        reply_markup=get_withdraw_methods_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "withdraw:method:bank")
async def select_bank(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    await state.update_data(method="bank")
    await state.set_state(WithdrawStates.entering_bank_name)
    
    await safe_edit_text(
        callback,
        "<b>Nama Bank</b>\n\nMasukkan nama bank Anda:\n<i>Contoh: BCA, Mandiri, BNI, BRI</i>",
        reply_markup=get_cancel_keyboard("withdraw:back")
    )
    await callback.answer()


@router.message(WithdrawStates.entering_bank_name)
async def process_bank_name(
    message: Message,
    state: FSMContext,
    **kwargs: Any
) -> None:
    bank_name = (message.text or "").strip().upper()
    
    await state.update_data(bank_name=bank_name)
    await state.set_state(WithdrawStates.entering_account_number)
    
    await message.answer(
        "<b>Nomor Rekening</b>\n\nMasukkan nomor rekening Anda:",
        reply_markup=get_cancel_keyboard("withdraw:back"),
        parse_mode="HTML"
    )


@router.message(WithdrawStates.entering_account_number)
async def process_account_number(
    message: Message,
    state: FSMContext,
    **kwargs: Any
) -> None:
    account_number = (message.text or "").strip()
    
    if not account_number.isdigit():
        await message.answer(
            format_error("Nomor rekening harus berupa angka."),
            reply_markup=get_cancel_keyboard("withdraw:back"),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(account_number=account_number)
    await state.set_state(WithdrawStates.entering_account_name)
    
    await message.answer(
        "<b>Nama Pemilik Rekening</b>\n\nMasukkan nama sesuai buku tabungan:",
        reply_markup=get_cancel_keyboard("withdraw:back"),
        parse_mode="HTML"
    )


@router.message(WithdrawStates.entering_account_name)
async def process_account_name(
    message: Message,
    state: FSMContext,
    **kwargs: Any
) -> None:
    account_name = (message.text or "").strip().upper()
    
    await state.update_data(account_name=account_name)
    await state.set_state(WithdrawStates.entering_amount)
    
    await message.answer(
        f"<b>Jumlah Withdraw</b>\n\nMasukkan jumlah (min Rp {MIN_WITHDRAW:,.0f}):",
        reply_markup=get_cancel_keyboard("withdraw:back"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "withdraw:method:ewallet")
async def select_ewallet(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    await state.update_data(method="ewallet")
    
    await safe_edit_text(
        callback,
        "<b>Pilih E-Wallet</b>\n\nPilih e-wallet tujuan:",
        reply_markup=get_ewallet_options_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("withdraw:ewallet:"))
async def select_ewallet_type(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    data = get_callback_data(callback)
    ewallet_type = data.split(":")[-1]
    
    await state.update_data(ewallet_type=ewallet_type)
    await state.set_state(WithdrawStates.entering_ewallet_number)
    
    await safe_edit_text(
        callback,
        f"<b>Nomor {ewallet_type}</b>\n\nMasukkan nomor {ewallet_type}:",
        reply_markup=get_cancel_keyboard("withdraw:back")
    )
    await callback.answer()


@router.message(WithdrawStates.entering_ewallet_number)
async def process_ewallet_number(
    message: Message,
    state: FSMContext,
    **kwargs: Any
) -> None:
    ewallet_number = (message.text or "").strip()
    
    await state.update_data(ewallet_number=ewallet_number)
    await state.set_state(WithdrawStates.entering_amount)
    
    await message.answer(
        f"<b>Jumlah Withdraw</b>\n\nMasukkan jumlah (min Rp {MIN_WITHDRAW:,.0f}):",
        reply_markup=get_cancel_keyboard("withdraw:back"),
        parse_mode="HTML"
    )


@router.message(WithdrawStates.entering_amount)
async def process_withdraw_amount(
    message: Message,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    amount = parse_amount(message.text or "")
    
    if not amount or amount < MIN_WITHDRAW:
        await message.answer(
            format_error(f"Jumlah minimal withdraw adalah Rp {MIN_WITHDRAW:,.0f}"),
            reply_markup=get_cancel_keyboard("withdraw:back"),
            parse_mode="HTML"
        )
        return
    
    if not user:
        await message.answer(format_error("User tidak ditemukan."), parse_mode="HTML")
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    
    if amount > balance:
        await message.answer(
            format_insufficient_balance(amount, balance),
            reply_markup=get_cancel_keyboard("withdraw:back"),
            parse_mode="HTML"
        )
        return
    
    state_data = await state.get_data()
    await state.update_data(amount=float(amount))
    
    if state_data.get("method") == "bank":
        confirm_text = (
            f"<b>Konfirmasi Withdraw</b>\n\n"
            f"{Emoji.DOT} Bank: {state_data['bank_name']}\n"
            f"{Emoji.DOT} No. Rek: {state_data['account_number']}\n"
            f"{Emoji.DOT} Nama: {state_data['account_name']}\n"
            f"{Emoji.DOT} Jumlah: Rp {amount:,.0f}\n\n"
            f"Lanjutkan withdraw?"
        )
    else:
        confirm_text = (
            f"<b>Konfirmasi Withdraw</b>\n\n"
            f"{Emoji.DOT} {state_data['ewallet_type']}: {state_data['ewallet_number']}\n"
            f"{Emoji.DOT} Jumlah: Rp {amount:,.0f}\n\n"
            f"Lanjutkan withdraw?"
        )
    
    await state.set_state(WithdrawStates.confirming)
    
    await message.answer(
        confirm_text,
        reply_markup=get_confirm_keyboard("withdraw", "confirm"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "withdraw:confirm:confirm")
async def confirm_withdraw(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    state_data = await state.get_data()
    amount = Decimal(str(state_data["amount"]))
    
    if not user:
        await callback.answer("User tidak ditemukan.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    
    if amount > balance:
        await safe_edit_text(
            callback,
            format_insufficient_balance(amount, balance),
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    if state_data.get("method") == "bank":
        withdrawal = await create_withdrawal(
            db=db,
            user_id=user.id,
            amount=amount,
            bank_name=state_data.get("bank_name"),
            account_number=state_data.get("account_number"),
            account_name=state_data.get("account_name"),
        )
    else:
        withdrawal = await create_withdrawal(
            db=db,
            user_id=user.id,
            amount=amount,
            ewallet_type=state_data.get("ewallet_type"),
            ewallet_number=state_data.get("ewallet_number"),
        )
    
    await state.clear()
    
    await safe_edit_text(
        callback,
        format_transaction_pending()
    )
    
    user_name = user.firstName or user.username or "User"
    msg = callback.message
    if msg is not None and hasattr(msg, 'bot') and msg.bot is not None:
        for admin_id in config.bot.admin_ids:
            try:
                if state_data.get("method") == "bank":
                    detail = f"Bank: {state_data['bank_name']}\nNo. Rek: {state_data['account_number']}\nNama: {state_data['account_name']}"
                else:
                    detail = f"{state_data['ewallet_type']}: {state_data['ewallet_number']}"
                
                await msg.bot.send_message(
                    admin_id,
                    f"<b>Request Withdraw Baru</b>\n\n"
                    f"{Emoji.DOT} User: {user_name} (ID: {user.telegramId})\n"
                    f"{Emoji.DOT} Jumlah: Rp {amount:,.0f}\n"
                    f"{detail}\n\n"
                    f"ID Withdraw: <code>{withdrawal.id}</code>",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    await callback.answer("Request withdraw berhasil dikirim!", show_alert=True)


@router.callback_query(F.data == "withdraw:cancel:confirm")
async def cancel_withdraw(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    await state.clear()
    
    await safe_edit_text(
        callback,
        "Withdraw dibatalkan.",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "withdraw:back")
async def back_to_withdraw_menu(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    await state.set_state(WithdrawStates.selecting_method)
    
    await safe_edit_text(
        callback,
        format_withdraw_menu(),
        reply_markup=get_withdraw_methods_keyboard()
    )
    await callback.answer()
