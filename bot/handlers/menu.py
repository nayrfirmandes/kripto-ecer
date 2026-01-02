from decimal import Decimal
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from prisma import Prisma

from bot.formatters.messages import format_referral_info, format_rates, format_profile, Emoji
from bot.keyboards.inline import CallbackData, get_back_keyboard, get_referral_keyboard
from bot.db.queries import get_referral_count, get_referral_bonus_earned, get_user_by_telegram_id
from bot.services.oxapay import OxaPayService
from bot.config import config

router = Router()

USD_TO_IDR = Decimal("16000")


@router.callback_query(F.data == CallbackData.MENU_RATES)
async def show_rates(callback: CallbackQuery, **kwargs):
    oxapay = OxaPayService(
        merchant_api_key=config.oxapay.merchant_api_key,
        payout_api_key=config.oxapay.payout_api_key,
        webhook_secret=config.oxapay.webhook_secret,
    )
    
    try:
        prices = await oxapay.get_prices()
    finally:
        await oxapay.close()
    
    if not prices:
        await callback.answer("Gagal mengambil harga. Coba lagi.", show_alert=True)
        return
    
    await callback.message.edit_text(
        format_rates(prices, USD_TO_IDR),
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.MENU_REFERRAL)
async def show_referral(callback: CallbackQuery, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    referral_count = await get_referral_count(db, user.id)
    bonus_earned = await get_referral_bonus_earned(db, user.id)
    
    await callback.message.edit_text(
        format_referral_info(user.referralCode, referral_count, bonus_earned),
        reply_markup=get_referral_keyboard(user.referralCode),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.MENU_HELP)
async def show_help(callback: CallbackQuery, **kwargs):
    help_text = """{info} <b>Bantuan</b>

<b>Cara Menggunakan:</b>

1. <b>Top Up Saldo</b>
   Transfer ke rekening kami, konfirmasi, tunggu approval.

2. <b>Beli Crypto</b>
   Pilih coin {arrow} Masukkan jumlah {arrow} Konfirmasi.

3. <b>Jual Crypto</b>
   Pilih coin {arrow} Kirim ke address kami {arrow} Saldo bertambah.

4. <b>Withdraw</b>
   Request withdraw {arrow} Tunggu proses {arrow} Dana terkirim.

{warning} <b>Penting:</b>
{dot} Pastikan alamat wallet benar
{dot} Transaksi crypto bersifat final
{dot} Simpan bukti transaksi""".format(
        info=Emoji.INFO,
        arrow=Emoji.ARROW,
        dot=Emoji.DOT,
        warning=Emoji.WARNING
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == CallbackData.MENU_PROFILE)
async def show_profile(callback: CallbackQuery, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    # Fetch fresh user data from database to show latest balance
    fresh_user = await get_user_by_telegram_id(db, callback.from_user.id)
    if not fresh_user:
        await callback.answer("User tidak ditemukan.", show_alert=True)
        return
    
    balance = fresh_user.balance.amount if fresh_user.balance else 0
    
    await callback.message.edit_text(
        format_profile(
            telegram_id=fresh_user.telegramId,
            username=fresh_user.username,
            first_name=fresh_user.firstName,
            email=fresh_user.email,
            whatsapp=fresh_user.whatsapp,
            status=fresh_user.status,
            referral_code=fresh_user.referralCode,
            created_at=fresh_user.createdAt,
            balance=balance
        ),
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
