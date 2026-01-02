from typing import Any, Optional, Dict
from datetime import datetime, timezone
from cachetools import TTLCache
import asyncio


class BotCache:
    def __init__(self):
        self.users: TTLCache = TTLCache(maxsize=10000, ttl=300)
        self.coin_settings: TTLCache = TTLCache(maxsize=100, ttl=60)
        self.payment_methods: TTLCache = TTLCache(maxsize=50, ttl=60)
        self.referral_settings: TTLCache = TTLCache(maxsize=10, ttl=60)
        self._lock = asyncio.Lock()
    
    def get_user(self, telegram_id: int) -> Optional[Any]:
        return self.users.get(telegram_id)
    
    def set_user(self, telegram_id: int, user: Any):
        self.users[telegram_id] = user
    
    def invalidate_user(self, telegram_id: int):
        self.users.pop(telegram_id, None)
    
    def get_coin_settings_all(self) -> Optional[list]:
        return self.coin_settings.get("all")
    
    def set_coin_settings_all(self, settings: list):
        self.coin_settings["all"] = settings
    
    def get_payment_methods_all(self) -> Optional[list]:
        return self.payment_methods.get("all")
    
    def set_payment_methods_all(self, methods: list):
        self.payment_methods["all"] = methods
    
    def get_referral_setting(self) -> Optional[Any]:
        return self.referral_settings.get("active")
    
    def set_referral_setting(self, setting: Any):
        self.referral_settings["active"] = setting


cache = BotCache()
