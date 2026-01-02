# pyright: reportReturnType=false
"""
Optimized API service with parallel requests and caching
"""

import asyncio
from decimal import Decimal
from typing import Optional, Dict, List, Any
from bot.services.oxapay import OxaPayService
from bot.services.cache import cache_service
from bot.config import config


class ParallelAPIService:
    """Handles parallel API calls to reduce response time"""
    
    @staticmethod
    async def get_coin_data_parallel(
        oxapay: OxaPayService,
        coin: str,
        network: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get coin networks AND exchange rate in PARALLEL
        Instead of: await networks, await rate (sequential: ~400-600ms)
        Do: await both together (~200-300ms)
        """
        try:
            # Run both requests in parallel
            networks_task = oxapay.get_coin_networks(coin)
            rate_task = oxapay.get_exchange_rate(coin, "USD")
            
            networks, rate_usd = await asyncio.gather(networks_task, rate_task, return_exceptions=True)
            
            # Handle exceptions
            if isinstance(networks, Exception):
                networks = None
            if isinstance(rate_usd, Exception):
                rate_usd = None
            
            return {
                "networks": networks,
                "rate_usd": rate_usd,
                "rate_idr": Decimal(str(rate_usd)) * Decimal(str(config.bot.usd_to_idr)) if rate_usd else None
            }
        except Exception as e:
            return {
                "networks": None,
                "rate_usd": None,
                "rate_idr": None,
                "error": str(e)
            }
    
    @staticmethod
    async def get_multiple_coins_data(
        oxapay: OxaPayService,
        coins: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple coins in parallel
        """
        tasks = [
            ParallelAPIService.get_coin_data_parallel(oxapay, coin)
            for coin in coins
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            coin: result if not isinstance(result, Exception) else {"error": str(result)}
            for coin, result in zip(coins, results)
        }
    
    @staticmethod
    async def get_exchange_rate_cached(
        oxapay: OxaPayService,
        coin: str,
        target: str = "USD",
        cache_key: Optional[str] = None
    ) -> Optional[Decimal]:
        """
        Get exchange rate with caching
        """
        if not cache_key:
            cache_key = f"rate:{coin}:{target}"
        
        # Try cache first
        cached_rate = cache_service.get_settings(cache_key)
        if cached_rate:
            return Decimal(str(cached_rate))
        
        try:
            rate = await oxapay.get_exchange_rate(coin, target)
            if rate:
                # Cache for 60 seconds
                cache_service.set_settings(cache_key, float(rate))
                return rate
        except Exception as e:
            print(f"Error getting exchange rate: {e}")
        
        return None
