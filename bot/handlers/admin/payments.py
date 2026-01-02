from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from prisma import Prisma

from bot.formatters.messages import Emoji
from bot.utils.telegram_helpers import get_callback_data
from bot.keyboards.admin import payment_list_keyboard, payment_type_keyboard, cancel_keyboard
from bot.handlers.admin.shared import AdminStates, is_admin, safe_edit_text

router = Router()


@router.callback_query(F.data == "admin:payments")
async def admin_payments(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    methods = await db.paymentmethod.find_many(order={"name": "asc"})
    
    text = "<b>Payment Methods</b>\n\n"
    payments: list[tuple[str, str, bool]] = []
    
    for m in methods:
        status = "ON" if m.isActive else "OFF"
        text += f"<b>{m.name}</b> ({m.type}) - {status}\n"
        text += f"{m.accountNo} - {m.accountName}\n\n"
        payments.append((m.id, m.name, m.isActive))
    
    if not methods:
        text += "Belum ada payment method.\n"
    
    await safe_edit_text(callback, text, reply_markup=payment_list_keyboard(payments))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggle_payment:"))
async def toggle_payment(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    payment_id = parts[2]
    
    payment = await db.paymentmethod.find_unique(where={"id": payment_id})
    
    if not payment:
        await callback.answer("Payment tidak ditemukan.", show_alert=True)
        return
    
    await db.paymentmethod.update(
        where={"id": payment_id},
        data={"isActive": not payment.isActive}
    )
    
    status = "disabled" if payment.isActive else "enabled"
    await callback.answer(f"{payment.name} {status}!", show_alert=True)
    
    await admin_payments(callback, db)


@router.callback_query(F.data == "admin:add_payment")
async def add_payment_start(callback: CallbackQuery, state: FSMContext, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    await state.set_state(AdminStates.adding_payment_name)
    
    await safe_edit_text(
        callback,
        "<b>Tambah Payment Method</b>\n\n"
        "Masukkan nama payment (contoh: BCA, Mandiri, DANA):",
        reply_markup=cancel_keyboard("admin:payments")
    )
    await callback.answer()


@router.message(AdminStates.adding_payment_name)
async def add_payment_name(message: Message, state: FSMContext, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nama tidak boleh kosong")
        return
    
    await state.update_data(payment_name=name)
    await state.set_state(AdminStates.adding_payment_type)
    
    await message.answer(
        f"Nama: <b>{name}</b>\n\n"
        "Pilih tipe payment:",
        parse_mode="HTML",
        reply_markup=payment_type_keyboard()
    )


@router.callback_query(F.data.startswith("payment_type:"))
async def add_payment_type(callback: CallbackQuery, state: FSMContext, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    payment_type = get_callback_data(callback).split(":")[-1]
    await state.update_data(payment_type=payment_type)
    await state.set_state(AdminStates.adding_payment_account_no)
    
    await safe_edit_text(
        callback,
        "<b>Tambah Payment Method</b>\n\n"
        "Masukkan nomor rekening/akun:",
        reply_markup=cancel_keyboard("admin:payments")
    )
    await callback.answer()


@router.message(AdminStates.adding_payment_account_no)
async def add_payment_account_no(message: Message, state: FSMContext, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    account_no = (message.text or "").strip()
    if not account_no:
        await message.answer("Nomor rekening tidak boleh kosong")
        return
    
    await state.update_data(account_no=account_no)
    await state.set_state(AdminStates.adding_payment_account_name)
    
    await message.answer("Masukkan nama pemilik rekening:")


@router.message(AdminStates.adding_payment_account_name)
async def add_payment_account_name(message: Message, state: FSMContext, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    account_name = (message.text or "").strip()
    if not account_name:
        await message.answer("Nama pemilik tidak boleh kosong")
        return
    
    data = await state.get_data()
    
    await db.paymentmethod.create(
        data={
            "name": data.get("payment_name", ""),
            "type": data.get("payment_type", "BANK"),
            "accountNo": data.get("account_no", ""),
            "accountName": account_name,
            "isActive": True,
        }
    )
    
    await state.clear()
    await message.answer(f"{Emoji.CHECK} Payment method berhasil ditambahkan!")
