from aiogram import Router, F
from aiogram.types import CallbackQuery
from prisma import Prisma

from bot.formatters.messages import Emoji, format_wib_datetime
from bot.keyboards.inline import CallbackData, get_history_pagination_keyboard, get_back_keyboard
from bot.db.queries import get_user_by_telegram_id, get_user_transactions, count_user_transactions

router = Router()

ITEMS_PER_PAGE = 10


@router.callback_query(F.data == CallbackData.MENU_HISTORY)
async def show_history(callback: CallbackQuery, db: Prisma, **kwargs):
    await show_history_page(callback, db, page=1)


@router.callback_query(F.data.startswith("history:page:"))
async def show_history_page_callback(callback: CallbackQuery, db: Prisma, **kwargs):
    page = int(callback.data.split(":")[-1])
    await show_history_page(callback, db, page=page)


async def show_history_page(callback: CallbackQuery, db: Prisma, page: int = 1):
    user = await get_user_by_telegram_id(db, callback.from_user.id)
    
    if not user:
        await callback.answer("Silakan daftar terlebih dahulu.", show_alert=True)
        return
    
    total_count = await count_user_transactions(db, user.id)
    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    offset = (page - 1) * ITEMS_PER_PAGE
    transactions = await get_user_transactions(db, user.id, limit=ITEMS_PER_PAGE, offset=offset)
    
    if not transactions:
        await callback.message.edit_text(
            f"{Emoji.CLOCK} <b>Riwayat Transaksi Anda</b>\n\nAnda belum memiliki riwayat transaksi.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    type_label = {
        "BUY": "Beli",
        "SELL": "Jual",
        "TOPUP": "Top Up",
        "WITHDRAW": "Withdraw",
        "REFERRAL_BONUS": "Bonus",
    }
    
    history_text = f"{Emoji.CLOCK} <b>Riwayat Transaksi Anda</b>\n\n"
    
    for tx in transactions:
        label = type_label.get(tx.type, tx.type)
        status_symbol = {
            "PENDING": "○",
            "PROCESSING": "◐",
            "COMPLETED": Emoji.CHECK,
            "FAILED": Emoji.CROSS,
            "CANCELLED": Emoji.CROSS,
        }.get(tx.status, "○")
        
        date_str = format_wib_datetime(tx.createdAt)
        
        history_text += f"{status_symbol} {label}: Rp {tx.amount:,.0f}\n   <i>{date_str}</i>\n"
    
    history_text += f"\n<i>Menampilkan halaman {page} dari {total_pages}</i>"
    
    await callback.message.edit_text(
        history_text,
        reply_markup=get_history_pagination_keyboard(page, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "history:current")
async def history_current(callback: CallbackQuery, **kwargs):
    await callback.answer()
