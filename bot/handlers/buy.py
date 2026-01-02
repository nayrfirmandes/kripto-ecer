from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma

from bot.formatters.messages import (
    format_buy_menu,
    format_coin_networks,
    format_buy_amount,
    format_buy_confirm,
    format_transaction_success,
    format_error,
    format_insufficient_balance,
    Emoji,
)
from bot.keyboards.inline import (
    CallbackData,
    get_coins_keyboard,
    get_networks_keyboard,
    get_confirm_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
)
from bot.utils.helpers import parse_amount, idr_to_crypto
from bot.services.oxapay import OxaPayService
from bot.db.optimized_queries import get_coin_settings_fast, get_active_networks_for_coin, get_active_coins
from bot.services.api_service import ParallelAPIService
from bot.tasks.background_tasks import schedule_background_task, process_payout_async
from bot.db.queries import (
    get_coin_settings,
    create_crypto_order,
    update_balance,
)
from bot.services.cache import cache_service
from bot.config import config

router = Router()

USD_TO_IDR = Decimal("16000")


class BuyStates(StatesGroup):
    selecting_coin = State()
    selecting_network = State()
    entering_amount = State()
    entering_wallet = State()
    confirming = State()


@router.callback_query(F.data == CallbackData.MENU_BUY)
async def show_buy_menu(callback: CallbackQuery, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    if not user or user.status != "ACTIVE":
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    await state.set_state(BuyStates.selecting_coin)
    
    # Get active coins from DATABASE (not OxaPay)
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await callback.message.edit_text(
        format_buy_menu(),
        reply_markup=get_coins_keyboard(coins, "buy"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:coin:"))
async def select_buy_coin(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
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
    await state.set_state(BuyStates.selecting_network)
    
    await callback.message.edit_text(
        format_coin_networks(coin),
        reply_markup=get_networks_keyboard(networks, coin, "buy", rate_idr),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:network:"))
async def select_buy_network(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    parts = callback.data.split(":")
    coin = parts[2]
    network = parts[3]
    
    # Use optimized cached version: ~1ms if cached, ~20-30ms if not (vs always ~50-100ms)
    coin_setting = await get_coin_settings_fast(db, coin, network)
    
    if not coin_setting:
        margin = Decimal("2")
    else:
        margin = coin_setting.buyMargin
    
    oxapay = OxaPayService(
        merchant_api_key=config.oxapay.merchant_api_key,
        payout_api_key=config.oxapay.payout_api_key,
        webhook_secret=config.oxapay.webhook_secret,
    )
    
    try:
        # Get rate AND networks in PARALLEL (reduces time from ~600ms to ~300ms)
        coin_data = await ParallelAPIService.get_coin_data_parallel(oxapay, coin)
        rate_usd = coin_data["rate_usd"]
        networks = coin_data["networks"]
    finally:
        await oxapay.close()
    
    if not rate_usd:
        await callback.answer("Gagal mendapatkan rate.", show_alert=True)
        return
    
    rate_idr = rate_usd * USD_TO_IDR
    
    network_info = next((n for n in networks if n["network"] == network), None)
    network_fee = network_info["withdraw_fee"] if network_info else Decimal("0")
    
    await state.update_data(
        coin=coin,
        network=network,
        rate_idr=float(rate_idr),
        margin=float(margin),
        network_fee=float(network_fee),
    )
    await state.set_state(BuyStates.entering_amount)
    
    await callback.message.edit_text(
        format_buy_amount(coin, network, rate_idr, margin),
        reply_markup=get_cancel_keyboard("buy:back"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BuyStates.entering_amount)
async def process_buy_amount(message: Message, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    amount_idr = parse_amount(message.text)
    
    if not amount_idr or amount_idr < Decimal("10000"):
        await message.answer(
            format_error("Jumlah minimal pembelian adalah Rp 10.000"),
            reply_markup=get_cancel_keyboard("buy:back"),
            parse_mode="HTML"
        )
        return
    
    if not user:
        await message.answer(format_error("User tidak ditemukan."), parse_mode="HTML")
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    
    data = await state.get_data()
    rate_idr = Decimal(str(data["rate_idr"]))
    margin = Decimal(str(data["margin"]))
    network_fee = Decimal(str(data["network_fee"]))
    
    calc = idr_to_crypto(amount_idr, rate_idr, margin, network_fee)
    
    if calc.get("error"):
        await message.answer(
            format_error(calc["error"]),
            reply_markup=get_cancel_keyboard("buy:back"),
            parse_mode="HTML"
        )
        return
    
    total_idr = calc["total_idr"]
    
    if total_idr > balance:
        await message.answer(
            format_insufficient_balance(total_idr, balance),
            reply_markup=get_cancel_keyboard("buy:back"),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(
        amount_idr=float(amount_idr),
        crypto_amount=float(calc["crypto_amount"]),
        total_idr=float(total_idr),
        network_fee_idr=float(calc["network_fee_idr"]),
    )
    await state.set_state(BuyStates.entering_wallet)
    
    await message.answer(
        f"<b>Alamat Wallet</b>\n\n"
        f"Masukkan alamat wallet {data['coin']} ({data['network']}):",
        reply_markup=get_cancel_keyboard("buy:back"),
        parse_mode="HTML"
    )


@router.message(BuyStates.entering_wallet)
async def process_wallet_address(message: Message, state: FSMContext, **kwargs):
    wallet = message.text.strip()
    
    if len(wallet) < 20:
        await message.answer(
            format_error("Alamat wallet tidak valid."),
            reply_markup=get_cancel_keyboard("buy:back"),
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    await state.update_data(wallet_address=wallet)
    await state.set_state(BuyStates.confirming)
    
    await message.answer(
        format_buy_confirm(
            coin=data["coin"],
            network=data["network"],
            fiat_amount=Decimal(str(data["amount_idr"])),
            crypto_amount=Decimal(str(data["crypto_amount"])),
            rate=Decimal(str(data["rate_idr"])) * (Decimal("1") + Decimal(str(data["margin"])) / Decimal("100")),
            network_fee=Decimal(str(data["network_fee"])),
            total=Decimal(str(data["total_idr"])),
        ),
        reply_markup=get_confirm_keyboard("buy", "process"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "buy:confirm:process")
async def confirm_buy(callback: CallbackQuery, state: FSMContext, db: Prisma, user: Optional[dict] = None, **kwargs):
    data = await state.get_data()
    
    if not user:
        await callback.answer("User tidak ditemukan.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    total_idr = Decimal(str(data["total_idr"]))
    
    if total_idr > balance:
        await callback.message.edit_text(
            format_insufficient_balance(total_idr, balance),
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # PARALLELIZE ALL DB OPERATIONS (100-200ms instead of 300-500ms)
    order, _ = await asyncio.gather(
        create_crypto_order(
            db=db,
            user_id=user.id,
            order_type="BUY",
            coin_symbol=data["coin"],
            network=data["network"],
            crypto_amount=Decimal(str(data["crypto_amount"])),
            fiat_amount=Decimal(str(data["amount_idr"])),
            rate=Decimal(str(data["rate_idr"])),
            margin=Decimal(str(data["margin"])),
            network_fee=Decimal(str(data["network_fee"])),
            wallet_address=data["wallet_address"],
            expires_at=datetime.utcnow() + timedelta(hours=24),
        ),
        update_balance(db, user.id, -total_idr)
    )
    
    # Update order status in parallel with user response
    async def update_order_status():
        await db.cryptoorder.update(
            where={"id": order.id},
            data={"status": "PROCESSING"}
        )
    
    # RESPOND IMMEDIATELY to user (100-200ms)
    await state.clear()
    
    await callback.message.edit_text(
        format_transaction_success("Beli Crypto", total_idr) + 
        f"\n\nAnda menerima: <b>{data['crypto_amount']:.8f} {data['coin']}</b>\n"
        f"Ke: <code>{data['wallet_address'][:20]}...</code>\n\n"
        f"<i>Memproses payout... Tunggu sebentar.</i>",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
    
    # PROCESS PAYOUT & UPDATE STATUS IN BACKGROUND (non-blocking)
    schedule_background_task(asyncio.gather(
        update_order_status(),
        process_payout_async(
            db=db,
            order_id=order.id,
            user_id=user.id,
            wallet_address=data["wallet_address"],
            amount=Decimal(str(data["crypto_amount"])),
            coin=data["coin"],
            network=data["network"],
            total_idr=total_idr,
        )
    ))


@router.callback_query(F.data == "buy:cancel:process")
async def cancel_buy(callback: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    
    await callback.message.edit_text(
        "Pembelian dibatalkan.",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "buy:back")
async def back_to_buy_coins(callback: CallbackQuery, state: FSMContext, db: Prisma, **kwargs):
    await state.set_state(BuyStates.selecting_coin)
    
    # Get active coins from DATABASE
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await callback.message.edit_text(
        format_buy_menu(),
        reply_markup=get_coins_keyboard(coins, "buy"),
        parse_mode="HTML"
    )
    await callback.answer()
