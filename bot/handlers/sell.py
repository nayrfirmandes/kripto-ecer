# pyright: basic
# type: ignore
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma

from bot.formatters.messages import (
    format_sell_menu,
    format_coin_networks,
    format_sell_confirm,
    format_error,
    Emoji,
)
from bot.keyboards.inline import (
    CallbackData,
    get_coins_keyboard,
    get_networks_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
)
from bot.utils.helpers import parse_crypto_amount, calculate_sell_price
from bot.services.oxapay import OxaPayService
from bot.db.optimized_queries import get_coin_settings_fast, get_active_networks_for_coin, get_active_coins
from bot.services.api_service import ParallelAPIService
from bot.db.queries import (
    get_coin_settings,
    create_crypto_order,
)
from bot.services.cache import cache_service
from bot.config import config

router = Router()

USD_TO_IDR = Decimal(str(config.bot.usd_to_idr))


class SellStates(StatesGroup):
    selecting_coin = State()
    selecting_network = State()
    entering_amount = State()
    awaiting_deposit = State()


@router.callback_query(F.data == CallbackData.MENU_SELL)
async def show_sell_menu(callback: CallbackQuery, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user or user.status != "ACTIVE":
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    await state.set_state(SellStates.selecting_coin)
    
    # Get active coins from DATABASE (not OxaPay)
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await callback.message.edit_text(
        format_sell_menu(),
        reply_markup=get_coins_keyboard(coins, "sell"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sell:coin:"))
async def select_sell_coin(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    coin = callback.data.split(":")[-1]
    
    # Get ACTIVE networks from DATABASE (for filtering)
    db_networks = await get_active_networks_for_coin(db, coin)
    
    if not db_networks:
        await callback.answer("Network tidak tersedia untuk coin ini.", show_alert=True)
        return
    
    # Get rate AND network fees from OxaPay
    oxapay = OxaPayService(
        merchant_api_key=config.oxapay.merchant_api_key,
        payout_api_key=config.oxapay.payout_api_key,
        webhook_secret=config.oxapay.webhook_secret,
    )
    
    try:
        coin_data = await ParallelAPIService.get_coin_data_parallel(oxapay, coin)
        rate_usd = coin_data["rate_usd"]
        oxapay_networks = coin_data["networks"]
    finally:
        await oxapay.close()
    
    rate_idr = rate_usd * USD_TO_IDR if rate_usd else None
    
    # Filter OxaPay networks to only show active ones from database
    active_network_names = {n["network"] for n in db_networks}
    networks = [n for n in oxapay_networks if n["network"] in active_network_names]
    
    if not networks:
        await callback.answer("Network tidak tersedia.", show_alert=True)
        return
    
    await state.update_data(coin=coin)
    await state.set_state(SellStates.selecting_network)
    
    await callback.message.edit_text(
        format_coin_networks(coin),
        reply_markup=get_networks_keyboard(networks, coin, "sell", rate_idr),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sell:network:"))
async def select_sell_network(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    parts = callback.data.split(":")
    coin = parts[2]
    network = parts[3]
    
    coin_setting = await get_coin_settings_fast(db, coin, network)
    
    if not coin_setting:
        margin = Decimal("2")
    else:
        margin = coin_setting.sellMargin
    
    oxapay = OxaPayService(
        merchant_api_key=config.oxapay.merchant_api_key,
        payout_api_key=config.oxapay.payout_api_key,
        webhook_secret=config.oxapay.webhook_secret,
    )
    
    try:
        rate_usd = await oxapay.get_exchange_rate(coin, "USD")
    finally:
        await oxapay.close()
    
    if not rate_usd:
        await callback.answer("Gagal mendapatkan rate.", show_alert=True)
        return
    
    rate_idr = rate_usd * USD_TO_IDR
    rate_with_margin = rate_idr * (Decimal("1") - margin / Decimal("100"))
    
    await state.update_data(
        coin=coin,
        network=network,
        rate_idr=float(rate_idr),
        margin=float(margin),
    )
    await state.set_state(SellStates.entering_amount)
    
    await callback.message.edit_text(
        f"<b>Jual {coin}</b> ({network})\n\n"
        f"Rate: <b>Rp {rate_with_margin:,.0f}</b> / {coin}\n"
        f"<i>Sudah termasuk margin {margin}%</i>\n\n"
        f"Masukkan jumlah {coin}:\n"
        f"<i>Contoh: 0.001</i>",
        reply_markup=get_cancel_keyboard("sell:back"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SellStates.entering_amount)
async def process_sell_amount(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    crypto_amount = parse_crypto_amount(message.text)
    
    if not crypto_amount or crypto_amount <= 0:
        await message.answer(
            format_error("Jumlah tidak valid."),
            reply_markup=get_cancel_keyboard("sell:back"),
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    rate_idr = Decimal(str(data["rate_idr"]))
    margin = Decimal(str(data["margin"]))
    
    calc = calculate_sell_price(crypto_amount, rate_idr, margin)
    fiat_amount = calc["total"]
    
    if fiat_amount < Decimal("10000"):
        await message.answer(
            format_error("Jumlah terlalu kecil. Minimum penjualan senilai Rp 10.000"),
            reply_markup=get_cancel_keyboard("sell:back"),
            parse_mode="HTML"
        )
        return
    
    if not user:
        await message.answer(format_error("User tidak ditemukan."), parse_mode="HTML")
        return
    
    oxapay = OxaPayService(
        merchant_api_key=config.oxapay.merchant_api_key,
        payout_api_key=config.oxapay.payout_api_key,
        webhook_secret=config.oxapay.webhook_secret,
    )
    
    try:
        result = await oxapay.create_static_address(
            currency=data["coin"],
            network=data["network"],
            callback_url=config.oxapay.webhook_url,
        )
        
        if not result.success:
            await message.answer(
                format_error(f"Gagal membuat address: {result.error}"),
                reply_markup=get_cancel_keyboard("sell:back"),
                parse_mode="HTML"
            )
            return
        
        order = await create_crypto_order(
            db=db,
            user_id=user.id,
            order_type="SELL",
            coin_symbol=data["coin"],
            network=data["network"],
            crypto_amount=crypto_amount,
            fiat_amount=fiat_amount,
            rate=rate_idr,
            margin=margin,
            network_fee=Decimal("0"),
            deposit_address=result.address,
            oxapay_payment_id=result.payment_id,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        await db.cryptoorder.update(
            where={"id": order.id},
            data={"status": "AWAITING_CRYPTO"}
        )
        
        await state.clear()
        
        await message.answer(
            format_sell_confirm(
                coin=data["coin"],
                network=data["network"],
                crypto_amount=crypto_amount,
                fiat_amount=fiat_amount,
                rate=calc["rate_with_margin"],
                deposit_address=result.address,
            ),
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            format_error(f"Terjadi kesalahan: {str(e)}"),
            reply_markup=get_cancel_keyboard("sell:back"),
            parse_mode="HTML"
        )
    finally:
        await oxapay.close()


@router.callback_query(F.data == "sell:back")
async def back_to_sell_coins(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    await state.set_state(SellStates.selecting_coin)
    
    # Get active coins from DATABASE
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await callback.message.edit_text(
        format_sell_menu(),
        reply_markup=get_coins_keyboard(coins, "sell"),
        parse_mode="HTML"
    )
    await callback.answer()
