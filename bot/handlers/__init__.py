from aiogram import Router

from .start import router as start_router
from .menu import router as menu_router
from .signup import router as signup_router
from .balance import router as balance_router
from .topup import router as topup_router
from .withdraw import router as withdraw_router
from .buy import router as buy_router
from .sell import router as sell_router
from .history import router as history_router
from .settings import router as settings_router
from .admin import router as admin_router
from .stock import router as stock_router
from .crypto_deposit import router as crypto_deposit_router


def setup_routers() -> Router:
    main_router = Router()
    
    main_router.include_router(start_router)
    main_router.include_router(signup_router)
    main_router.include_router(menu_router)
    main_router.include_router(balance_router)
    main_router.include_router(topup_router)
    main_router.include_router(withdraw_router)
    main_router.include_router(buy_router)
    main_router.include_router(sell_router)
    main_router.include_router(history_router)
    main_router.include_router(settings_router)
    main_router.include_router(admin_router)
    main_router.include_router(stock_router)
    main_router.include_router(crypto_deposit_router)
    
    return main_router
