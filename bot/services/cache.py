from typing import Optional, Any, Dict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from cachetools import TTLCache
import asyncio


class CacheService:
    """High-performance caching service for reducing DB queries"""
    
    def __init__(self):
        # Balance cache: fastest path (TTL: 5 seconds for real-time feel)
        self._balance_cache: TTLCache = TTLCache(maxsize=5000, ttl=5)
        
        # Coin settings cache: shorter TTL for faster sync with admin changes (TTL: 10 seconds)
        self._coin_settings_cache: TTLCache = TTLCache(maxsize=100, ttl=10)
        
        # User settings cache: stable data (TTL: 30 seconds)
        self._settings_cache: TTLCache = TTLCache(maxsize=1000, ttl=30)
        
        # Referral count cache: fast but updates less frequently (TTL: 15 seconds)
        self._referral_cache: TTLCache = TTLCache(maxsize=2000, ttl=15)
        
        # OxaPay coins cache: avoid expensive API calls (TTL: 10 seconds)
        self._coins_cache: TTLCache = TTLCache(maxsize=1, ttl=10)
        
        # Generic cache for custom keys with manual expiry
        self._generic_cache: Dict[str, Any] = {}
    
    def get_balance(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached balance - O(1) operation"""
        return self._balance_cache.get(user_id)
    
    def set_balance(self, user_id: str, balance: Dict[str, Any]):
        """Cache balance data"""
        self._balance_cache[user_id] = balance
    
    def invalidate_balance(self, user_id: str):
        """Invalidate balance cache when balance changes"""
        self._balance_cache.pop(user_id, None)
    
    def get_coin_settings(self, coin: str, network: str) -> Optional[Dict[str, Any]]:
        """Get cached coin settings - O(1) operation"""
        key = f"{coin}:{network}"
        return self._coin_settings_cache.get(key)
    
    def set_coin_settings(self, coin: str, network: str, settings: Dict[str, Any]):
        """Cache coin settings"""
        key = f"{coin}:{network}"
        self._coin_settings_cache[key] = settings
    
    def invalidate_coin_settings(self, coin: str = None, network: str = None):
        """Invalidate coin settings cache"""
        if coin and network:
            key = f"{coin}:{network}"
            self._coin_settings_cache.pop(key, None)
        else:
            self._coin_settings_cache.clear()
    
    def get_settings(self, settings_key: str) -> Optional[Any]:
        """Get cached system settings"""
        return self._settings_cache.get(settings_key)
    
    def set_settings(self, settings_key: str, value: Any):
        """Cache system settings"""
        self._settings_cache[settings_key] = value
    
    def invalidate_settings(self, settings_key: str = None):
        """Invalidate settings cache"""
        if settings_key:
            self._settings_cache.pop(settings_key, None)
        else:
            self._settings_cache.clear()
    
    def get_referral_count(self, user_id: str) -> Optional[int]:
        """Get cached referral count"""
        return self._referral_cache.get(f"ref_count:{user_id}")
    
    def set_referral_count(self, user_id: str, count: int):
        """Cache referral count"""
        self._referral_cache[f"ref_count:{user_id}"] = count
    
    def invalidate_referral(self, user_id: str):
        """Invalidate referral cache"""
        self._referral_cache.pop(f"ref_count:{user_id}", None)
    
    def get_coins(self) -> Optional[list]:
        """Get cached supported coins from OxaPay"""
        return self._coins_cache.get("supported_coins")
    
    def set_coins(self, coins: list):
        """Cache supported coins"""
        self._coins_cache["supported_coins"] = coins
    
    def invalidate_coins(self):
        """Invalidate coins cache"""
        self._coins_cache.pop("supported_coins", None)
    
    def get_generic(self, key: str) -> Optional[Any]:
        """Get value from generic cache with manual expiry check"""
        import time
        cached = self._generic_cache.get(key)
        if cached and cached.get("expires", 0) > time.time():
            return cached.get("data")
        return None
    
    def set_generic(self, key: str, data: Any, ttl: int = 10):
        """Set value in generic cache with TTL in seconds"""
        import time
        self._generic_cache[key] = {
            "data": data,
            "expires": time.time() + ttl
        }
    
    def clear_all(self):
        """Clear all caches"""
        self._balance_cache.clear()
        self._coin_settings_cache.clear()
        self._settings_cache.clear()
        self._referral_cache.clear()
        self._coins_cache.clear()
        self._generic_cache.clear()


# Global cache instance
cache_service = CacheService()
