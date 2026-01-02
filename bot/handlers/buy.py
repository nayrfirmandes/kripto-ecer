from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Any
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prisma import Prisma
from prisma.models import User

from bot.formatters.messages import (
    format_buy_menu,
    format_coin_networks,
    format_buy_amount,
    format_buy_confirm,
    format_transaction_success,
    format_error,
    format_insufficient_balance,
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
from bot.utils.telegram_helpers import safe_edit_text, get_callback_data
from bot.services.oxapay import OxaPayService
from bot.db.optimized_queries import get_coin_settings_fast, get_active_networks_for_coin, get_active_coins
from bot.services.api_service import ParallelAPIService
from bot.tasks.background_tasks import schedule_background_task, process_payout_async
from bot.db.queries import (
    create_crypto_order,
    update_balance,
)
from bot.config import config

router = Router()

USD_TO_IDR = Decimal(str(config.bot.usd_to_idr))


class BuyStates(StatesGroup):
    selecting_coin = State()
    selecting_network = State()
    entering_amount = State()
    entering_wallet = State()
    confirming = State()


@router.callback_query(F.data == CallbackData.MENU_BUY)
async def show_buy_menu(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    if not user or user.status != "ACTIVE":
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    await state.set_state(BuyStates.selecting_coin)
    
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await safe_edit_text(
        callback,
        format_buy_menu(),
        reply_markup=get_coins_keyboard(coins, "buy")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:coin:"))
async def select_buy_coin(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    **kwargs: Any
) -> None:
    data = get_callback_data(callback)
    coin = data.split(":")[-1]
    
    db_networks = await get_active_networks_for_coin(db, coin)
    
    if not db_networks:
        await callback.answer("Network tidak tersedia untuk coin ini.", show_alert=True)
        return
    
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
    
    active_network_names = {n["network"] for n in db_networks}
    networks = [n for n in oxapay_networks if n["network"] in active_network_names]
    
    if not networks:
        await callback.answer("Network tidak tersedia.", show_alert=True)
        return
    
    await state.update_data(coin=coin)
    await state.set_state(BuyStates.selecting_network)
    
    await safe_edit_text(
        callback,
        format_coin_networks(coin),
        reply_markup=get_networks_keyboard(networks, coin, "buy", rate_idr)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:network:"))
async def select_buy_network(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    **kwargs: Any
) -> None:
    data = get_callback_data(callback)
    parts = data.split(":")
    coin = parts[2]
    network = parts[3]
    
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
    
    await safe_edit_text(
        callback,
        format_buy_amount(coin, network, rate_idr, margin),
        reply_markup=get_cancel_keyboard("buy:back")
    )
    await callback.answer()


@router.message(BuyStates.entering_amount)
async def process_buy_amount(
    message: Message,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    amount_idr = parse_amount(message.text or "")
    
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
    
    state_data = await state.get_data()
    rate_idr = Decimal(str(state_data["rate_idr"]))
    margin = Decimal(str(state_data["margin"]))
    network_fee = Decimal(str(state_data["network_fee"]))
    
    calc = idr_to_crypto(amount_idr, rate_idr, margin, network_fee)
    
    if calc.get("error"):
        await message.answer(
            format_error(str(calc["error"])),
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
        f"Masukkan alamat wallet {state_data['coin']} ({state_data['network']}):",
        reply_markup=get_cancel_keyboard("buy:back"),
        parse_mode="HTML"
    )


@router.message(BuyStates.entering_wallet)
async def process_wallet_address(
    message: Message,
    state: FSMContext,
    **kwargs: Any
) -> None:
    wallet = (message.text or "").strip()
    
    if len(wallet) < 20:
        await message.answer(
            format_error("Alamat wallet tidak valid."),
            reply_markup=get_cancel_keyboard("buy:back"),
            parse_mode="HTML"
        )
        return
    
    state_data = await state.get_data()
    await state.update_data(wallet_address=wallet)
    await state.set_state(BuyStates.confirming)
    
    await message.answer(
        format_buy_confirm(
            coin=state_data["coin"],
            network=state_data["network"],
            fiat_amount=Decimal(str(state_data["amount_idr"])),
            crypto_amount=Decimal(str(state_data["crypto_amount"])),
            rate=Decimal(str(state_data["rate_idr"])) * (Decimal("1") + Decimal(str(state_data["margin"])) / Decimal("100")),
            network_fee=Decimal(str(state_data["network_fee"])),
            total=Decimal(str(state_data["total_idr"])),
        ),
        reply_markup=get_confirm_keyboard("buy", "process"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "buy:confirm:process")
async def confirm_buy(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    user: Optional[User] = None,
    **kwargs: Any
) -> None:
    state_data = await state.get_data()
    
    if not user:
        await callback.answer("User tidak ditemukan.", show_alert=True)
        return
    
    balance = user.balance.amount if user.balance else Decimal("0")
    total_idr = Decimal(str(state_data["total_idr"]))
    
    if total_idr > balance:
        await safe_edit_text(
            callback,
            format_insufficient_balance(total_idr, balance),
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    order, _ = await asyncio.gather(
        create_crypto_order(
            db=db,
            user_id=user.id,
            order_type="BUY",
            coin_symbol=state_data["coin"],
            network=state_data["network"],
            crypto_amount=Decimal(str(state_data["crypto_amount"])),
            fiat_amount=Decimal(str(state_data["amount_idr"])),
            rate=Decimal(str(state_data["rate_idr"])),
            margin=Decimal(str(state_data["margin"])),
            network_fee=Decimal(str(state_data["network_fee"])),
            wallet_address=state_data["wallet_address"],
            expires_at=datetime.utcnow() + timedelta(hours=24),
        ),
        update_balance(db, user.id, -total_idr)
    )
    
    async def update_order_status() -> None:
        await db.cryptoorder.update(
            where={"id": order.id},
            data={"status": "PROCESSING"}
        )
    
    await state.clear()
    
    await safe_edit_text(
        callback,
        format_transaction_success("Beli Crypto", total_idr) + 
        f"\n\nAnda menerima: <b>{state_data['crypto_amount']:.8f} {state_data['coin']}</b>\n"
        f"Ke: <code>{state_data['wallet_address'][:20]}...</code>\n\n"
        f"<i>Memproses payout... Tunggu sebentar.</i>",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
    
    schedule_background_task(asyncio.gather(
        update_order_status(),
        process_payout_async(
            db=db,
            order_id=order.id,
            user_id=user.id,
            wallet_address=state_data["wallet_address"],
            amount=Decimal(str(state_data["crypto_amount"])),
            coin=state_data["coin"],
            network=state_data["network"],
            total_idr=total_idr,
        )
    ))


@router.callback_query(F.data == "buy:cancel:process")
async def cancel_buy(
    callback: CallbackQuery,
    state: FSMContext,
    **kwargs: Any
) -> None:
    await state.clear()
    
    await safe_edit_text(
        callback,
        "Pembelian dibatalkan.",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "buy:back")
async def back_to_buy_coins(
    callback: CallbackQuery,
    state: FSMContext,
    db: Prisma,
    **kwargs: Any
) -> None:
    await state.set_state(BuyStates.selecting_coin)
    
    coins = await get_active_coins(db)
    
    if not coins:
        await callback.answer("Tidak ada coin tersedia.", show_alert=True)
        return
    
    await safe_edit_text(
        callback,
        format_buy_menu(),
        reply_markup=get_coins_keyboard(coins, "buy")
    )
    await callback.answer()
