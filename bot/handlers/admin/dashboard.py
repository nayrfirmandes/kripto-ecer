from typing import Any, cast
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from prisma import Prisma
from prisma.enums import TransactionStatus, UserStatus

from bot.formatters.messages import Emoji
from bot.db.queries import update_balance
from bot.utils.telegram_helpers import get_callback_data
from bot.keyboards.admin import back_to_admin_keyboard
from bot.handlers.admin.shared import is_admin, safe_edit_text

router = Router()


@router.callback_query(F.data == "admin:dashboard")
async def admin_dashboard(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    pending_deposits = await db.deposit.count(where={"status": TransactionStatus.PENDING})
    pending_withdrawals = await db.withdrawal.count(where={"status": TransactionStatus.PENDING})
    total_users = await db.user.count()
    active_users = await db.user.count(where={"status": UserStatus.ACTIVE})
    
    completed_deposits = await db.deposit.find_many(where={"status": TransactionStatus.COMPLETED})
    completed_withdrawals = await db.withdrawal.find_many(where={"status": TransactionStatus.COMPLETED})
    
    dep_sum = sum(d.amount for d in completed_deposits)
    wit_sum = sum(w.amount for w in completed_withdrawals)
    
    await safe_edit_text(
        callback,
        f"📊 <b>DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>👥 USERS</b>\n"
        f"   Total     : <b>{total_users:,}</b>\n"
        f"   Active    : <b>{active_users:,}</b>\n\n"
        f"<b>⏳ PENDING</b>\n"
        f"   Topup     : <b>{pending_deposits}</b>\n"
        f"   Withdraw  : <b>{pending_withdrawals}</b>\n\n"
        f"<b>💰 TOTAL VOLUME</b>\n"
        f"   Deposits  : <b>Rp {dep_sum:,.0f}</b>\n"
        f"   Withdraws : <b>Rp {wit_sum:,.0f}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="admin:dashboard")],
            [InlineKeyboardButton(text="← Back", callback_data="admin:menu")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin:pending_topup")
async def pending_topup_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    deposits = await db.deposit.find_many(
        where={"status": TransactionStatus.PENDING},
        include={"user": True},
        order={"createdAt": "asc"},
        take=10,
    )
    
    if not deposits:
        await safe_edit_text(
            callback,
            "Tidak ada pending top up.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Refresh", callback_data="admin:pending_topup")],
                [InlineKeyboardButton(text="Back", callback_data="admin:menu")]
            ])
        )
        await callback.answer()
        return
    
    buttons: list[list[InlineKeyboardButton]] = []
    text = "<b>Pending Top Up</b>\n\n"
    
    for d in deposits:
        user = d.user
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
        else:
            user_name = "Unknown"
        
        text += (
            f"<b>ID:</b> <code>{d.id[:8]}</code>\n"
            f"<b>User:</b> {user_name}\n"
            f"<b>Amount:</b> Rp {d.amount:,.0f}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"✅ {d.id[:8]}", callback_data=f"admin:approve_topup:{d.id}"),
            InlineKeyboardButton(text=f"❌ {d.id[:8]}", callback_data=f"admin:reject_topup:{d.id}"),
        ])
    
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="admin:menu")])
    
    await safe_edit_text(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "admin:pending_withdraw")
async def pending_withdraw_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    withdrawals = await db.withdrawal.find_many(
        where={"status": TransactionStatus.PENDING},
        include={"user": True},
        order={"createdAt": "asc"},
        take=10
    )
    
    if not withdrawals:
        await safe_edit_text(
            callback,
            "Tidak ada pending withdraw.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Refresh", callback_data="admin:pending_withdraw")],
                [InlineKeyboardButton(text="Back", callback_data="admin:menu")]
            ])
        )
        await callback.answer()
        return
    
    buttons: list[list[InlineKeyboardButton]] = []
    text = "<b>Pending Withdraw</b>\n\n"
    
    for w in withdrawals:
        user = w.user
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
        else:
            user_name = "Unknown"
        
        text += (
            f"<b>ID:</b> <code>{w.id[:8]}</code>\n"
            f"<b>User:</b> {user_name}\n"
            f"<b>Amount:</b> Rp {w.amount:,.0f}\n"
            f"<b>Bank:</b> {w.bankName}\n"
            f"<b>No Rek:</b> {w.accountNumber}\n"
            f"<b>Nama:</b> {w.accountName}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"✅ {w.id[:8]}", callback_data=f"admin:approve_withdraw:{w.id}"),
            InlineKeyboardButton(text=f"❌ {w.id[:8]}", callback_data=f"admin:reject_withdraw:{w.id}"),
        ])
    
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="admin:menu")])
    
    await safe_edit_text(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:approve_topup:"))
async def approve_topup_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    deposit_id = parts[2]
    
    deposit = await db.deposit.find_unique(
        where={"id": deposit_id},
        include={"user": True}
    )
    
    if not deposit:
        await callback.answer("Deposit tidak ditemukan.", show_alert=True)
        return
    
    if deposit.status != TransactionStatus.PENDING:
        await callback.answer("Deposit sudah diproses.", show_alert=True)
        return
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["depositId"], "equals": deposit_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    user = deposit.user
    if user:
        await update_balance(db, user.id, deposit.amount)
    
    await callback.answer(f"Topup Rp {deposit.amount:,.0f} approved!", show_alert=True)
    
    if user is not None and callback.bot is not None:
        try:
            await callback.bot.send_message(
                user.telegramId,
                f"<b>Topup Berhasil</b> {Emoji.CHECK}\n\n"
                f"Rp {deposit.amount:,.0f} telah ditambahkan ke saldo Anda.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await pending_topup_callback(callback, db)


@router.callback_query(F.data.startswith("admin:reject_topup:"))
async def reject_topup_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    deposit_id = parts[2]
    
    deposit = await db.deposit.find_unique(
        where={"id": deposit_id},
        include={"user": True}
    )
    
    if not deposit:
        await callback.answer("Deposit tidak ditemukan.", show_alert=True)
        return
    
    if deposit.status != TransactionStatus.PENDING:
        await callback.answer("Deposit sudah diproses.", show_alert=True)
        return
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": TransactionStatus.FAILED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["depositId"], "equals": deposit_id}}),
        data={"status": TransactionStatus.FAILED}
    )
    
    await callback.answer("Topup rejected!", show_alert=True)
    
    user = deposit.user
    if user is not None and callback.bot is not None:
        try:
            await callback.bot.send_message(
                user.telegramId,
                f"<b>Topup Ditolak</b> {Emoji.CROSS}\n\n"
                f"Topup Rp {deposit.amount:,.0f} ditolak.\n"
                f"Hubungi admin untuk info lebih lanjut.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await pending_topup_callback(callback, db)


@router.callback_query(F.data.startswith("admin:approve_withdraw:"))
async def approve_withdraw_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    withdrawal_id = parts[2]
    
    withdrawal = await db.withdrawal.find_unique(
        where={"id": withdrawal_id},
        include={"user": True}
    )
    
    if not withdrawal:
        await callback.answer("Withdrawal tidak ditemukan.", show_alert=True)
        return
    
    if withdrawal.status != TransactionStatus.PENDING:
        await callback.answer("Withdrawal sudah diproses.", show_alert=True)
        return
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await callback.answer(f"Withdraw Rp {withdrawal.amount:,.0f} approved!", show_alert=True)
    
    user = withdrawal.user
    if user is not None and callback.bot is not None:
        try:
            await callback.bot.send_message(
                user.telegramId,
                f"<b>Withdraw Berhasil</b> {Emoji.CHECK}\n\n"
                f"Rp {withdrawal.amount:,.0f} telah dikirim ke rekening Anda.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await pending_withdraw_callback(callback, db)


@router.callback_query(F.data.startswith("admin:reject_withdraw:"))
async def reject_withdraw_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    withdrawal_id = parts[2]
    
    withdrawal = await db.withdrawal.find_unique(
        where={"id": withdrawal_id},
        include={"user": True}
    )
    
    if not withdrawal:
        await callback.answer("Withdrawal tidak ditemukan.", show_alert=True)
        return
    
    if withdrawal.status != TransactionStatus.PENDING:
        await callback.answer("Withdrawal sudah diproses.", show_alert=True)
        return
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": TransactionStatus.FAILED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}}),
        data={"status": TransactionStatus.FAILED}
    )
    
    await callback.answer("Withdraw rejected!", show_alert=True)
    
    user = withdrawal.user
    if user is not None and callback.bot is not None:
        try:
            await callback.bot.send_message(
                user.telegramId,
                f"<b>Withdraw Ditolak</b> {Emoji.CROSS}\n\n"
                f"Withdraw Rp {withdrawal.amount:,.0f} ditolak.\n"
                f"Hubungi admin untuk info lebih lanjut.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await pending_withdraw_callback(callback, db)
