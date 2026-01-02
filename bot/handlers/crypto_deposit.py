from decimal import Decimal
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma

from bot.formatters.messages import Emoji
from bot.keyboards.inline import CallbackData, get_back_keyboard, get_cancel_keyboard
from bot.services.cryptobot import CryptoBotService
from bot.db.queries import create_deposit
from bot.config import config

router = Router()

MIN_DEPOSIT = Decimal("1")
MARGIN = Decimal("0.05")


class CryptoDepositStates(StatesGroup):
    selecting_coin = State()
    entering_amount = State()
    confirming = State()


def get_cryptobot() -> CryptoBotService:
    return CryptoBotService(
        api_token=config.cryptobot.api_token,
        margin=config.cryptobot.margin,
    )


def get_crypto_deposit_keyboard():
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="₮ USDT", callback_data="crypto_deposit:coin:USDT"),
        InlineKeyboardButton(text="◉ USDC", callback_data="crypto_deposit:coin:USDC"),
    )
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.MENU_TOPUP),
    )
    return builder.as_markup()


def get_pay_keyboard(pay_url: str, deposit_id: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Bayar via CryptoBot", url=pay_url),
    )
    builder.row(
        InlineKeyboardButton(text="✅ Sudah Bayar", callback_data=f"crypto_deposit:check:{deposit_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Batal", callback_data=f"crypto_deposit:cancel:{deposit_id}"),
    )
    return builder.as_markup()


@router.callback_query(F.data == "topup:method:crypto")
async def show_crypto_deposit(callback: CallbackQuery, state: FSMContext, **kwargs):
    if not config.cryptobot.api_token:
        await callback.answer("Deposit crypto belum tersedia.", show_alert=True)
        return
    
    await state.set_state(CryptoDepositStates.selecting_coin)
    
    margin_pct = int(config.cryptobot.margin * 100)
    
    await callback.message.edit_text(
        f"{Emoji.COIN} <b>Deposit via CryptoBot</b>\n\n"
        f"Pilih cryptocurrency untuk deposit:\n\n"
        f"<i>Fee: {margin_pct}% dari jumlah deposit</i>",
        reply_markup=get_crypto_deposit_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("crypto_deposit:coin:"))
async def select_crypto_coin(callback: CallbackQuery, state: FSMContext, **kwargs):
    coin = callback.data.split(":")[-1]
    
    await state.update_data(coin=coin, prompt_msg_id=callback.message.message_id)
    await state.set_state(CryptoDepositStates.entering_amount)
    
    await callback.message.edit_text(
        f"{Emoji.COIN} <b>Deposit {coin}</b>\n\n"
        f"Masukkan jumlah {coin} yang ingin didepositkan:\n\n"
        f"<i>Minimal: {MIN_DEPOSIT} {coin}</i>",
        reply_markup=get_cancel_keyboard("topup:method:crypto"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CryptoDepositStates.entering_amount)
async def process_crypto_amount(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    try:
        await message.delete()
    except:
        pass
    
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
    except:
        sent = await message.answer(
            f"{Emoji.CROSS} Format jumlah tidak valid. Gunakan angka.",
            reply_markup=get_cancel_keyboard("topup:method:crypto"),
            parse_mode="HTML"
        )
        return
    
    if amount < MIN_DEPOSIT:
        sent = await message.answer(
            f"{Emoji.CROSS} Jumlah minimal adalah {MIN_DEPOSIT}",
            reply_markup=get_cancel_keyboard("topup:method:crypto"),
            parse_mode="HTML"
        )
        return
    
    if not user:
        await message.answer(f"{Emoji.CROSS} User tidak ditemukan.", parse_mode="HTML")
        return
    
    data = await state.get_data()
    coin = data.get("coin", "USDT")
    prompt_msg_id = data.get("prompt_msg_id")
    
    if prompt_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prompt_msg_id)
        except:
            pass
    
    cryptobot = get_cryptobot()
    
    try:
        result = await cryptobot.create_invoice(
            asset=coin,
            amount=amount,
            description=f"Deposit {amount} {coin} - @kriptoecerbot",
            expires_in=3600,
        )
        
        if not result.success:
            await message.answer(
                f"{Emoji.CROSS} Gagal membuat invoice: {result.error}",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            return
        
        idr_rate = await cryptobot.get_idr_rate(coin)
        gross_idr = amount * idr_rate
        fee_idr = gross_idr * MARGIN
        net_idr = gross_idr - fee_idr
        
        deposit = await create_deposit(
            db=db,
            user_id=user.id,
            amount=net_idr,
            payment_method=f"CryptoBot {coin}",
        )
        
        await db.deposit.update(
            where={"id": deposit.id},
            data={"cryptobotInvoiceId": result.invoice_id}
        )
        
        await state.update_data(
            deposit_id=deposit.id,
            invoice_id=result.invoice_id,
            amount=float(amount),
            amount_idr=float(net_idr),
        )
        await state.set_state(CryptoDepositStates.confirming)
        
        margin_pct = int(MARGIN * 100)
        
        await message.answer(
            f"{Emoji.COIN} <b>Invoice Deposit {coin}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Deposit: <b>{amount} {coin}</b>\n"
            f"Rate: <b>Rp {idr_rate:,.0f}/{coin}</b>\n"
            f"Gross: <b>Rp {gross_idr:,.0f}</b>\n"
            f"Fee ({margin_pct}%): <b>-Rp {fee_idr:,.0f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Saldo diterima: <b>Rp {net_idr:,.0f}</b>\n\n"
            f"Klik tombol untuk bayar via @CryptoBot:",
            reply_markup=get_pay_keyboard(result.pay_url, deposit.id),
            parse_mode="HTML"
        )
        
        for admin_id in config.bot.admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"<b>Request Deposit Crypto Baru</b>\n\n"
                    f"{Emoji.DOT} User: {user.firstName or user.username} (ID: {user.telegramId})\n"
                    f"{Emoji.DOT} Deposit: {amount} {coin}\n"
                    f"{Emoji.DOT} Gross: Rp {gross_idr:,.0f}\n"
                    f"{Emoji.DOT} Fee 5%: Rp {fee_idr:,.0f}\n"
                    f"{Emoji.DOT} Net: Rp {net_idr:,.0f}\n"
                    f"{Emoji.DOT} Invoice: {result.invoice_id}\n\n"
                    f"ID: <code>{deposit.id}</code>",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        
    finally:
        await cryptobot.close()


@router.callback_query(F.data.startswith("crypto_deposit:check:"))
async def check_crypto_payment(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    deposit_id = callback.data.split(":")[-1]
    
    deposit = await db.deposit.find_unique(where={"id": deposit_id})
    
    if not deposit:
        await callback.answer("Deposit tidak ditemukan.", show_alert=True)
        return
    
    if deposit.status == "COMPLETED":
        await callback.answer("Deposit sudah berhasil diproses!", show_alert=True)
        await state.clear()
        return
    
    if not deposit.cryptobotInvoiceId:
        await callback.answer("Invoice tidak ditemukan.", show_alert=True)
        return
    
    cryptobot = get_cryptobot()
    
    try:
        invoice = await cryptobot.get_invoice(deposit.cryptobotInvoiceId)
        
        if not invoice:
            await callback.answer("Tidak dapat mengecek status pembayaran.", show_alert=True)
            return
        
        status = invoice.get("status", "")
        
        if status == "paid":
            await db.deposit.update(
                where={"id": deposit_id},
                data={"status": "COMPLETED"}
            )
            
            await db.balance.update(
                where={"userId": deposit.userId},
                data={"amount": {"increment": deposit.amount}}
            )
            
            await state.clear()
            
            await callback.message.edit_text(
                f"{Emoji.CHECK} <b>Deposit Berhasil!</b>\n\n"
                f"Saldo Anda telah ditambah <b>Rp {deposit.amount:,.0f}</b>",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("Pembayaran berhasil!", show_alert=True)
        
        elif status == "expired":
            await db.deposit.update(
                where={"id": deposit_id},
                data={"status": "FAILED"}
            )
            await state.clear()
            
            await callback.message.edit_text(
                f"{Emoji.CROSS} <b>Invoice Expired</b>\n\n"
                f"Invoice sudah kadaluarsa. Silakan buat deposit baru.",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("Invoice expired.", show_alert=True)
        
        else:
            await callback.answer(f"Status: {status}. Silakan selesaikan pembayaran.", show_alert=True)
    
    finally:
        await cryptobot.close()


@router.callback_query(F.data.startswith("crypto_deposit:cancel:"))
async def cancel_crypto_deposit(callback: CallbackQuery, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    from bot.formatters.messages import format_main_menu
    from bot.keyboards.inline import get_main_menu_keyboard
    
    deposit_id = callback.data.split(":")[-1]
    
    deposit = await db.deposit.find_unique(where={"id": deposit_id})
    
    if not deposit:
        await callback.answer("Deposit tidak ditemukan.", show_alert=True)
        return
    
    if deposit.status == "COMPLETED":
        await callback.answer("Deposit sudah selesai diproses.", show_alert=True)
        return
    
    if deposit.cryptobotInvoiceId:
        cryptobot = get_cryptobot()
        try:
            invoice = await cryptobot.get_invoice(deposit.cryptobotInvoiceId)
            status = invoice.get("status", "")
            
            if status == "paid":
                await db.deposit.update(
                    where={"id": deposit_id},
                    data={"status": "COMPLETED"}
                )
                await db.balance.update(
                    where={"userId": deposit.userId},
                    data={"amount": {"increment": deposit.amount}}
                )
                await state.clear()
                
                await callback.message.edit_text(
                    f"{Emoji.CHECK} <b>Deposit Berhasil!</b>\n\n"
                    f"Pembayaran terdeteksi. Saldo ditambah <b>Rp {deposit.amount:,.0f}</b>",
                    reply_markup=get_back_keyboard(),
                    parse_mode="HTML"
                )
                await callback.answer("Pembayaran sudah diterima!", show_alert=True)
                return
        finally:
            await cryptobot.close()
    
    await db.deposit.update(
        where={"id": deposit_id},
        data={"status": "CANCELLED"}
    )
    
    await state.clear()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    if user and user.status == "ACTIVE":
        balance = user.balance.amount if user.balance else 0
        name = user.firstName or user.username or "User"
        
        await callback.message.answer(
            format_main_menu(balance, name, callback.from_user.id),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()
