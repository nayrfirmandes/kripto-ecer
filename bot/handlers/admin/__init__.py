from aiogram import Router

from bot.handlers.admin.menu import router as menu_router
from bot.handlers.admin.dashboard import router as dashboard_router
from bot.handlers.admin.coins import router as coins_router
from bot.handlers.admin.payments import router as payments_router
from bot.handlers.admin.referrals import router as referrals_router
from bot.handlers.admin.users import router as users_router
from bot.handlers.admin.commands import router as commands_router

router = Router()

router.include_router(menu_router)
router.include_router(dashboard_router)
router.include_router(coins_router)
router.include_router(payments_router)
router.include_router(referrals_router)
router.include_router(users_router)
router.include_router(commands_router)
