from decimal import Decimal
from typing import Any, Optional, cast
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from prisma import Prisma
from prisma.enums import TransactionStatus, UserStatus

from bot.formatters.messages import Emoji
from bot.db.queries import update_balance
from bot.utils.telegram_helpers import get_callback_data
from bot.config import config

router = Router()


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


def is_admin(user_id: Optional[int]) -> bool:
    if user_id is None:
        return False
    return user_id in config.bot.admin_ids


def admin_menu_keyboard(pending_topup: int = 0, pending_withdraw: int = 0) -> InlineKeyboardMarkup:
    topup_text = f"📥 Topup ({pending_topup})" if pending_topup > 0 else "📥 Topup"
    withdraw_text = f"📤 Withdraw ({pending_withdraw})" if pending_withdraw > 0 else "📤 Withdraw"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Dashboard", callback_data="admin:dashboard"),
        ],
        [
            InlineKeyboardButton(text=topup_text, callback_data="admin:pending_topup"),
            InlineKeyboardButton(text=withdraw_text, callback_data="admin:pending_withdraw"),
        ],
        [
            InlineKeyboardButton(text="🪙 Coins", callback_data="admin:coins"),
            InlineKeyboardButton(text="💳 Payments", callback_data="admin:payments"),
        ],
        [
            InlineKeyboardButton(text="👥 Users", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton(text="← Menu Utama", callback_data="back:menu"),
        ],
    ])


@router.message(Command("admin"))
async def admin_menu(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    pending_topup = await db.deposit.count(where={"status": TransactionStatus.PENDING})
    pending_withdraw = await db.withdrawal.count(where={"status": TransactionStatus.PENDING})
    total_users = await db.user.count()
    
    await message.answer(
        f"🔐 <b>ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📥 Pending Topup: <b>{pending_topup}</b>\n"
        f"📤 Pending Withdraw: <b>{pending_withdraw}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di bawah:",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(pending_topup, pending_withdraw)
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    pending_topup = await db.deposit.count(where={"status": TransactionStatus.PENDING})
    pending_withdraw = await db.withdrawal.count(where={"status": TransactionStatus.PENDING})
    total_users = await db.user.count()
    
    await safe_edit_text(
        callback,
        f"🔐 <b>ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📥 Pending Topup: <b>{pending_topup}</b>\n"
        f"📤 Pending Withdraw: <b>{pending_withdraw}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di bawah:",
        reply_markup=admin_menu_keyboard(pending_topup, pending_withdraw)
    )
    await callback.answer()


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
            f"<b>{user_name}</b>\n"
            f"Rp {d.amount:,.0f} via {d.paymentMethod}\n"
            f"<code>{d.id}</code>\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"Approve {d.amount:,.0f}", callback_data=f"admin:approve_topup:{d.id}"),
            InlineKeyboardButton(text="Reject", callback_data=f"admin:reject_topup:{d.id}"),
        ])
    
    buttons.append([InlineKeyboardButton(text="Refresh", callback_data="admin:pending_topup")])
    buttons.append([InlineKeyboardButton(text="Back", callback_data="admin:menu")])
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
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
        take=10,
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
        if w.bankName:
            dest = f"{w.bankName} - {w.accountNumber}"
        else:
            dest = f"{w.ewalletType} - {w.ewalletNumber}"
        
        user = w.user
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
        else:
            user_name = "Unknown"
        
        text += (
            f"<b>{user_name}</b>\n"
            f"Rp {w.amount:,.0f} ke {dest}\n"
            f"<code>{w.id}</code>\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"Approve {w.amount:,.0f}", callback_data=f"admin:approve_withdraw:{w.id}"),
            InlineKeyboardButton(text="Reject", callback_data=f"admin:reject_withdraw:{w.id}"),
        ])
    
    buttons.append([InlineKeyboardButton(text="Refresh", callback_data="admin:pending_withdraw")])
    buttons.append([InlineKeyboardButton(text="Back", callback_data="admin:menu")])
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
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
    
    await update_balance(db, deposit.userId, deposit.amount)
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["depositId"], "equals": deposit_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await callback.answer(f"Topup Rp {deposit.amount:,.0f} approved!", show_alert=True)
    
    user = deposit.user
    if user is not None and callback.bot is not None:
        try:
            await callback.bot.send_message(
                user.telegramId,
                f"<b>Top Up Berhasil</b> {Emoji.CHECK}\n\n"
                f"Saldo Anda telah ditambah <b>Rp {deposit.amount:,.0f}</b>",
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
                f"<b>Top Up Ditolak</b> {Emoji.CROSS}\n\n"
                f"Top up Rp {deposit.amount:,.0f} ditolak.\n"
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
    
    user_balance = await db.balance.find_unique(where={"userId": withdrawal.userId})
    
    if not user_balance or user_balance.amount < withdrawal.amount:
        await callback.answer("Saldo user tidak cukup.", show_alert=True)
        return
    
    await update_balance(db, withdrawal.userId, -withdrawal.amount)
    
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


@router.callback_query(F.data == "admin:coins")
async def admin_coins(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    coins = await db.coinsetting.find_many(order={"coinSymbol": "asc"})
    
    text = "<b>Coin Settings</b>\n\n"
    
    for coin in coins:
        status = "ON" if coin.isActive else "OFF"
        text += (
            f"<b>{coin.coinSymbol}</b> ({coin.network})\n"
            f"Buy: {coin.buyMargin}% | Sell: {coin.sellMargin}% | {status}\n\n"
        )
    
    buttons: list[list[InlineKeyboardButton]] = []
    unique_coins = list(set(c.coinSymbol for c in coins))
    for symbol in sorted(unique_coins):
        buttons.append([InlineKeyboardButton(text=f"Edit {symbol}", callback_data=f"admin:coin:{symbol}")])
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data="admin:menu")])
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:coin:"))
async def admin_coin_detail(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    symbol = parts[2]
    
    coins = await db.coinsetting.find_many(
        where={"coinSymbol": symbol},
        order={"network": "asc"}
    )
    
    text = f"<b>{symbol} Networks</b>\n\n"
    buttons: list[list[InlineKeyboardButton]] = []
    
    for coin in coins:
        status = "ON" if coin.isActive else "OFF"
        text += f"{coin.network}: Buy {coin.buyMargin}% | Sell {coin.sellMargin}% | {status}\n"
        
        toggle_text = "Disable" if coin.isActive else "Enable"
        buttons.append([
            InlineKeyboardButton(text=f"{coin.network}: {toggle_text}", callback_data=f"admin:toggle_coin:{coin.id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data="admin:coins")])
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggle_coin:"))
async def toggle_coin(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    data = get_callback_data(callback)
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("Invalid data", show_alert=True)
        return
    
    coin_id = parts[2]
    
    coin = await db.coinsetting.find_unique(where={"id": coin_id})
    
    if not coin:
        await callback.answer("Coin tidak ditemukan.", show_alert=True)
        return
    
    await db.coinsetting.update(
        where={"id": coin_id},
        data={"isActive": not coin.isActive}
    )
    
    status = "disabled" if coin.isActive else "enabled"
    await callback.answer(f"{coin.coinSymbol} {coin.network} {status}!", show_alert=True)
    
    new_callback_data = f"admin:coin:{coin.coinSymbol}"
    original_data = callback.data
    callback.data = new_callback_data
    await admin_coin_detail(callback, db)
    callback.data = original_data


@router.callback_query(F.data == "admin:payments")
async def admin_payments(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    methods = await db.paymentmethod.find_many(order={"name": "asc"})
    
    text = "<b>Payment Methods</b>\n\n"
    buttons: list[list[InlineKeyboardButton]] = []
    
    for m in methods:
        status = "ON" if m.isActive else "OFF"
        text += f"<b>{m.name}</b> ({m.type}) - {status}\n"
        text += f"{m.accountNo} - {m.accountName}\n\n"
        
        toggle_text = "Disable" if m.isActive else "Enable"
        buttons.append([
            InlineKeyboardButton(text=f"{m.name}: {toggle_text}", callback_data=f"admin:toggle_payment:{m.id}")
        ])
    
    if not methods:
        text += "Belum ada payment method.\n"
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data="admin:menu")])
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
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
    
    method = await db.paymentmethod.find_unique(where={"id": payment_id})
    
    if not method:
        await callback.answer("Payment method tidak ditemukan.", show_alert=True)
        return
    
    await db.paymentmethod.update(
        where={"id": payment_id},
        data={"isActive": not method.isActive}
    )
    
    status = "disabled" if method.isActive else "enabled"
    await callback.answer(f"{method.name} {status}!", show_alert=True)
    
    await admin_payments(callback, db)


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, db: Prisma, **kwargs: Any) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return
    
    users = await db.user.find_many(
        include={"balance": True},
        order={"createdAt": "desc"},
        take=20,
    )
    
    text = "<b>Recent Users</b> (showing 20)\n\n"
    
    for u in users:
        balance = u.balance.amount if u.balance else Decimal("0")
        text += (
            f"<b>{u.firstName or 'N/A'} {u.lastName or ''}</b>\n"
            f"@{u.username or 'N/A'} | Rp {balance:,.0f} | {u.status}\n\n"
        )
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back", callback_data="admin:menu")]
        ])
    )
    await callback.answer()


@router.message(Command("pending_topup"))
async def pending_topup(message: Message, db: Prisma, **kwargs: Any) -> None:
    from_user = message.from_user
    if from_user is None or not is_admin(from_user.id):
        return
    
    deposits = await db.deposit.find_many(
        where={"status": TransactionStatus.PENDING},
        include={"user": True},
        order={"createdAt": "asc"},
        take=20,
    )
    
    if not deposits:
        await message.answer("Tidak ada pending top up.")
        return
    
    text = "<b>Pending Top Up</b>\n\n"
    
    for d in deposits:
        user = d.user
        user_name = "Unknown"
        user_tg_id = 0
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
            user_tg_id = user.telegramId
        text += (
            f"ID: <code>{d.id}</code>\n"
            f"User: {user_name} ({user_tg_id})\n"
            f"Amount: Rp {d.amount:,.0f}\n"
            f"Via: {d.paymentMethod}\n"
            f"Date: {d.createdAt.strftime('%d/%m/%Y %H:%M')}\n\n"
        )
    
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
        
        user = w.user
        user_name = "Unknown"
        user_tg_id = 0
        if user is not None:
            user_name = user.firstName or user.username or "Unknown"
            user_tg_id = user.telegramId
        
        text += (
            f"ID: <code>{w.id}</code>\n"
            f"User: {user_name} ({user_tg_id})\n"
            f"Amount: Rp {w.amount:,.0f}\n"
            f"{dest}\n"
            f"Date: {w.createdAt.strftime('%d/%m/%Y %H:%M')}\n\n"
        )
    
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
    
    await update_balance(db, deposit.userId, deposit.amount)
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["depositId"], "equals": deposit_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    user = deposit.user
    user_name = "Unknown"
    if user is not None:
        user_name = user.firstName or user.username or "Unknown"
    
    await message.answer(
        f"{Emoji.CHECK} Top up approved!\n"
        f"User: {user_name}\n"
        f"Amount: Rp {deposit.amount:,.0f}"
    )
    
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Top Up Berhasil</b> {Emoji.CHECK}\n\n"
                f"Saldo Anda telah ditambah <b>Rp {deposit.amount:,.0f}</b>",
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
    
    await message.answer(f"{Emoji.CHECK} Top up rejected!")
    
    user = deposit.user
    if user is not None and message.bot is not None:
        try:
            await message.bot.send_message(
                user.telegramId,
                f"<b>Top Up Ditolak</b> {Emoji.CROSS}\n\n"
                f"Top up Rp {deposit.amount:,.0f} ditolak.\n"
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
    
    user_balance = await db.balance.find_unique(where={"userId": withdrawal.userId})
    
    if not user_balance or user_balance.amount < withdrawal.amount:
        await message.answer("Saldo user tidak cukup.")
        return
    
    await update_balance(db, withdrawal.userId, -withdrawal.amount)
    
    await db.withdrawal.update(
        where={"id": withdrawal_id},
        data={"status": TransactionStatus.COMPLETED}
    )
    
    await db.transaction.update_many(
        where=cast(Any, {"metadata": {"path": ["withdrawalId"], "equals": withdrawal_id}}),
        data={"status": TransactionStatus.COMPLETED}
    )
    
    user = withdrawal.user
    user_name = "Unknown"
    if user is not None:
        user_name = user.firstName or user.username or "Unknown"
    
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
