from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from prisma import Prisma

from bot.formatters.messages import Emoji
from bot.db.queries import update_balance
from bot.config import config

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.bot.admin_ids


@router.message(Command("admin"))
async def admin_menu(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    pending_deposits = await db.deposit.count(where={"status": "PENDING"})
    pending_withdrawals = await db.withdrawal.count(where={"status": "PENDING"})
    total_users = await db.user.count()
    active_users = await db.user.count(where={"status": "ACTIVE"})
    
    await message.answer(
        f"<b>Admin Panel</b>\n\n"
        f"{Emoji.DOT} Users: {total_users} (Active: {active_users})\n"
        f"{Emoji.DOT} Pending Top Up: {pending_deposits}\n"
        f"{Emoji.DOT} Pending Withdraw: {pending_withdrawals}\n\n"
        f"<b>Commands:</b>\n"
        f"/pending_topup - /pending_withdraw\n"
        f"/approve_topup [id] - /reject_topup [id]\n"
        f"/approve_withdraw [id] - /reject_withdraw [id]",
        parse_mode="HTML"
    )


@router.message(Command("pending_topup"))
async def pending_topup(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    deposits = await db.deposit.find_many(
        where={"status": "PENDING"},
        include={"user": True},
        order={"createdAt": "asc"},
        take=20,
    )
    
    if not deposits:
        await message.answer("Tidak ada pending top up.")
        return
    
    text = "<b>Pending Top Up</b>\n\n"
    
    for d in deposits:
        text += (
            f"ID: <code>{d.id}</code>\n"
            f"User: {d.user.firstName or d.user.username} ({d.user.telegramId})\n"
            f"Amount: Rp {d.amount:,.0f}\n"
            f"Via: {d.paymentMethod}\n"
            f"Date: {d.createdAt.strftime('%d/%m/%Y %H:%M')}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("pending_withdraw"))
async def pending_withdraw(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    withdrawals = await db.withdrawal.find_many(
        where={"status": "PENDING"},
        include={"user": True},
        order={"createdAt": "asc"},
        take=20,
    )
    
    if not withdrawals:
        await message.answer("Tidak ada pending withdraw.")
        return
    
    text = "<b>Pending Withdraw</b>\n\n"
    
    for w in withdrawals:
        if w.bankName:
            dest = f"Bank: {w.bankName} - {w.accountNumber} ({w.accountName})"
        else:
            dest = f"E-Wallet: {w.ewalletType} - {w.ewalletNumber}"
        
        text += (
            f"ID: <code>{w.id}</code>\n"
            f"User: {w.user.firstName or w.user.username} ({w.user.telegramId})\n"
            f"Amount: Rp {w.amount:,.0f}\n"
            f"{dest}\n"
            f"Date: {w.createdAt.strftime('%d/%m/%Y %H:%M')}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("approve_topup"))
async def approve_topup(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /approve_topup [deposit_id]")
        return
    
    deposit_id = args[1]
    
    deposit = await db.deposit.find_unique(
        where={"id": deposit_id},
        include={"user": True}
    )
    
    if not deposit:
        await message.answer("Deposit tidak ditemukan.")
        return
    
    if deposit.status != "PENDING":
        await message.answer("Deposit sudah diproses.")
        return
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": "COMPLETED"}
    )
    
    await update_balance(db, deposit.userId, deposit.amount)
    
    await db.transaction.update_many(
        where={"metadata": {"path": ["depositId"], "equals": deposit_id}},
        data={"status": "COMPLETED"}
    )
    
    await message.answer(
        f"{Emoji.CHECK} Top up approved!\n"
        f"User: {deposit.user.firstName or deposit.user.username}\n"
        f"Amount: Rp {deposit.amount:,.0f}"
    )
    
    try:
        await message.bot.send_message(
            deposit.user.telegramId,
            f"<b>Top Up Berhasil</b> {Emoji.CHECK}\n\n"
            f"Saldo Anda telah ditambah <b>Rp {deposit.amount:,.0f}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.message(Command("reject_topup"))
async def reject_topup(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /reject_topup [deposit_id]")
        return
    
    deposit_id = args[1]
    
    deposit = await db.deposit.find_unique(
        where={"id": deposit_id},
        include={"user": True}
    )
    
    if not deposit:
        await message.answer("Deposit tidak ditemukan.")
        return
    
    if deposit.status != "PENDING":
        await message.answer("Deposit sudah diproses.")
        return
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": "FAILED"}
    )
    
    await db.transaction.update_many(
        where={"metadata": {"path": ["depositId"], "equals": deposit_id}},
        data={"status": "FAILED"}
    )
    
    await message.answer(f"{Emoji.CHECK} Top up rejected!")
    
    try:
        await message.bot.send_message(
            deposit.user.telegramId,
            f"<b>Top Up Ditolak</b> {Emoji.CROSS}\n\n"
            f"Top up Rp {deposit.amount:,.0f} ditolak.\n"
            f"Hubungi admin untuk info lebih lanjut.",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.message(Command("approve_withdraw"))
async def approve_withdraw(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /approve_withdraw [withdrawal_id]")
        return
    
    withdrawal_id = args[1]
    
    withdrawal = await db.withdrawal.find_unique(
        where={"id": withdrawal_id},
        include={"user": True}
    )
    
    if not withdrawal:
        await message.answer("Withdrawal tidak ditemukan.")
        return
    
    if withdrawal.status != "PENDING":
        await message.answer("Withdrawal sudah diproses.")
        return
    
    user_balance = await db.balance.find_unique(where={"userId": withdrawal.userId})
    
    if not user_balance or user_balance.amount < withdrawal.amount:
        await message.answer("Saldo user tidak cukup.")
        return
    
    await update_balance(db, withdrawal.userId, -withdrawal.amount)
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": "COMPLETED"}
    )
    
    await db.transaction.update_many(
        where={"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}},
        data={"status": "COMPLETED"}
    )
    
    await message.answer(
        f"{Emoji.CHECK} Withdraw approved!\n"
        f"User: {withdrawal.user.firstName or withdrawal.user.username}\n"
        f"Amount: Rp {withdrawal.amount:,.0f}"
    )
    
    try:
        await message.bot.send_message(
            withdrawal.user.telegramId,
            f"<b>Withdraw Berhasil</b> {Emoji.CHECK}\n\n"
            f"Rp {withdrawal.amount:,.0f} telah dikirim ke rekening Anda.",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.message(Command("reject_withdraw"))
async def reject_withdraw(message: Message, db: Prisma, **kwargs):
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /reject_withdraw [withdrawal_id]")
        return
    
    withdrawal_id = args[1]
    
    withdrawal = await db.withdrawal.find_unique(
        where={"id": withdrawal_id},
        include={"user": True}
    )
    
    if not withdrawal:
        await message.answer("Withdrawal tidak ditemukan.")
        return
    
    if withdrawal.status != "PENDING":
        await message.answer("Withdrawal sudah diproses.")
        return
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": "FAILED"}
    )
    
    await db.transaction.update_many(
        where={"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}},
        data={"status": "FAILED"}
    )
    
    await message.answer(f"{Emoji.CHECK} Withdraw rejected!")
    
    try:
        await message.bot.send_message(
            withdrawal.user.telegramId,
            f"<b>Withdraw Ditolak</b> {Emoji.CROSS}\n\n"
            f"Withdraw Rp {withdrawal.amount:,.0f} ditolak.\n"
            f"Hubungi admin untuk info lebih lanjut.",
            parse_mode="HTML"
        )
    except Exception:
        pass
