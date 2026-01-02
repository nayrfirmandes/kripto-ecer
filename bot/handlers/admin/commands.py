from typing import Any, cast
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from prisma import Prisma
from prisma.enums import TransactionStatus

from bot.formatters.messages import Emoji
from bot.db.queries import update_balance
from bot.handlers.admin.shared import is_admin

router = Router()


@router.message(Command("pending_topup"))
async def pending_topup(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    deposits = await db.deposit.find_many(
        where={"status": TransactionStatus.PENDING},
        include={"user": True},
        order={"createdAt": "asc"},
        take=10
    )
    
    if not deposits:
        await message.answer("Tidak ada topup pending.")
        return
    
    text = "📥 <b>Pending Topup</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for d in deposits:
        user = d.user
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
        else:
            user_name = "Unknown"
        text += (
            f"<b>ID:</b> <code>{d.id}</code>\n"
            f"<b>User:</b> {user_name}\n"
            f"<b>Amount:</b> Rp {d.amount:,.0f}\n\n"
        )
    
    text += "Use /approve_topup [id] or /reject_topup [id]"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("pending_withdraw"))
async def pending_withdraw(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    withdrawals = await db.withdrawal.find_many(
        where={"status": TransactionStatus.PENDING},
        include={"user": True},
        order={"createdAt": "asc"},
        take=10
    )
    
    if not withdrawals:
        await message.answer("Tidak ada withdraw pending.")
        return
    
    text = "📤 <b>Pending Withdraw</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for w in withdrawals:
        user = w.user
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
        else:
            user_name = "Unknown"
        text += (
            f"<b>ID:</b> <code>{w.id}</code>\n"
            f"<b>User:</b> {user_name}\n"
            f"<b>Amount:</b> Rp {w.amount:,.0f}\n"
            f"<b>Bank:</b> {w.bankName}\n"
            f"<b>No Rek:</b> {w.accountNumber}\n"
            f"<b>Nama:</b> {w.accountName}\n\n"
        )
    
    text += "Use /approve_withdraw [id] or /reject_withdraw [id]"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("approve_topup"))
async def approve_topup(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    text = message.text or ""
    args = text.split()
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
    
    if deposit.status != TransactionStatus.PENDING:
        await message.answer("Deposit sudah diproses.")
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
    user_name = (user.firstName or user.username or "Unknown") if user else "Unknown"
    
    if user:
        await update_balance(db, user.id, deposit.amount)
    
    await message.answer(
        f"{Emoji.CHECK} Topup approved!\n"
        f"User: {user_name}\n"
        f"Amount: Rp {deposit.amount:,.0f}"
    )
    
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Topup Berhasil</b> {Emoji.CHECK}\n\n"
                f"Rp {deposit.amount:,.0f} telah ditambahkan ke saldo Anda.",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.message(Command("reject_topup"))
async def reject_topup(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    text = message.text or ""
    args = text.split()
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
    
    if deposit.status != TransactionStatus.PENDING:
        await message.answer("Deposit sudah diproses.")
        return
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": TransactionStatus.FAILED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["depositId"], "equals": deposit_id}}),
        data={"status": TransactionStatus.FAILED}
    )
    
    await message.answer(f"{Emoji.CHECK} Topup rejected!")
    
    user = deposit.user
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Topup Ditolak</b> {Emoji.CROSS}\n\n"
                f"Topup Rp {deposit.amount:,.0f} ditolak.\n"
                f"Hubungi admin untuk info lebih lanjut.",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.message(Command("approve_withdraw"))
async def approve_withdraw(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    text = message.text or ""
    args = text.split()
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
    
    if withdrawal.status != TransactionStatus.PENDING:
        await message.answer("Withdrawal sudah diproses.")
        return
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    user = withdrawal.user
    user_name = (user.firstName or user.username or "Unknown") if user else "Unknown"
    
    await message.answer(
        f"{Emoji.CHECK} Withdraw approved!\n"
        f"User: {user_name}\n"
        f"Amount: Rp {withdrawal.amount:,.0f}"
    )
    
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Withdraw Berhasil</b> {Emoji.CHECK}\n\n"
                f"Rp {withdrawal.amount:,.0f} telah dikirim ke rekening Anda.",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.message(Command("reject_withdraw"))
async def reject_withdraw(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    text = message.text or ""
    args = text.split()
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
    
    if withdrawal.status != TransactionStatus.PENDING:
        await message.answer("Withdrawal sudah diproses.")
        return
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": TransactionStatus.FAILED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}}),
        data={"status": TransactionStatus.FAILED}
    )
    
    await message.answer(f"{Emoji.CHECK} Withdraw rejected!")
    
    user = withdrawal.user
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Withdraw Ditolak</b> {Emoji.CROSS}\n\n"
                f"Withdraw Rp {withdrawal.amount:,.0f} ditolak.\n"
                f"Hubungi admin untuk info lebih lanjut.",
                parse_mode="HTML"
            )
        except Exception:
            pass
