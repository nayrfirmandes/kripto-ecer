from aiogram import Router, F
from aiogram.types import CallbackQuery
from decimal import Decimal

from bot.services.oxapay import OxaPayService
from bot.keyboards.inline import CallbackData, get_back_keyboard
from bot.formatters.messages import Emoji

router = Router()


def format_stock_message(balances: dict, prices: dict) -> str:
    lines = [
        f"{Emoji.CHART} <b>Stock Crypto Realtime</b>",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    supported_coins = ["BTC", "ETH", "BNB", "SOL", "USDT", "USDC"]
    total_usd = Decimal("0")
    
    for coin in supported_coins:
        balance = Decimal(str(balances.get(coin, 0)))
        price = Decimal(str(prices.get(coin, 0)))
        value_usd = balance * price
        total_usd += value_usd
        
        if coin in ["USDT", "USDC"]:
            balance_str = f"{balance:,.2f}"
            value_str = f"${value_usd:,.2f}"
        else:
            balance_str = f"{balance:,.8f}".rstrip('0').rstrip('.')
            value_str = f"${value_usd:,.2f}"
        
        coin_emoji = get_coin_emoji(coin)
        lines.append(f"{coin_emoji} <b>{coin}</b>")
        lines.append(f"   Stock: {balance_str}")
        lines.append(f"   Value: {value_str}")
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{Emoji.MONEY} <b>Total Value:</b> ${total_usd:,.2f}")
    lines.append("")
    lines.append("<i>Data realtime dari custody wallet</i>")
    
    return "\n".join(lines)


def get_coin_emoji(coin: str) -> str:
    emojis = {
        "BTC": "₿",
        "ETH": "Ξ",
        "BNB": "◈",
        "SOL": "◎",
        "USDT": "₮",
        "USDC": "◉",
    }
    return emojis.get(coin, "•")


@router.callback_query(F.data == CallbackData.MENU_STOCK)
async def show_stock(callback: CallbackQuery, oxapay: OxaPayService, **kwargs):
    await callback.answer()
    
    await callback.message.edit_text(
        f"{Emoji.CLOCK} Mengambil data stock dari wallet...",
        parse_mode="HTML"
    )
    
    try:
        balances = await oxapay.get_balance()
        prices = await oxapay.get_prices()
        
        message = format_stock_message(balances, prices)
        
        await callback.message.edit_text(
            message,
            reply_markup=get_stock_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"{Emoji.CROSS} Gagal mengambil data stock.\n\nError: {str(e)}",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "stock:refresh")
async def refresh_stock(callback: CallbackQuery, oxapay: OxaPayService, **kwargs):
    await callback.answer("Memperbarui data...")
    
    try:
        balances = await oxapay.get_balance()
        prices = await oxapay.get_prices()
        
        message = format_stock_message(balances, prices)
        
        await callback.message.edit_text(
            message,
            reply_markup=get_stock_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"{Emoji.CROSS} Gagal memperbarui data stock.\n\nError: {str(e)}",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )


def get_stock_keyboard():
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Refresh", callback_data="stock:refresh"),
    )
    builder.row(
        InlineKeyboardButton(text="← Kembali", callback_data=CallbackData.BACK_MENU),
    )
    return builder.as_markup()
