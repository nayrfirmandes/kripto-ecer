import aiohttp
import hashlib
import hmac
import json
import time
from decimal import Decimal
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class CurrencyInfo:
    symbol: str
    name: str
    networks: dict[str, dict]


@dataclass
class PaymentResult:
    success: bool
    payment_id: Optional[str] = None
    address: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PayoutResult:
    success: bool
    payout_id: Optional[str] = None
    tx_hash: Optional[str] = None
    error: Optional[str] = None


_currencies_cache: dict = {}
_currencies_cache_time: float = 0
_prices_cache: dict = {}
_prices_cache_time: float = 0
CACHE_TTL = 30


class OxaPayService:
    BASE_URL = "https://api.oxapay.com"
    
    def __init__(self, merchant_api_key: str, payout_api_key: str, webhook_secret: str = ""):
        self.merchant_api_key = merchant_api_key
        self.payout_api_key = payout_api_key
        self.webhook_secret = webhook_secret
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        use_payout_key: bool = False
    ) -> dict:
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        api_key = self.payout_api_key if use_payout_key else self.merchant_api_key
        headers = {
            "Content-Type": "application/json",
            "merchant_api_key": api_key
        }
        
        try:
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    return await resp.json()
            else:
                payload = data or {}
                async with session.post(url, json=payload, headers=headers) as resp:
                    return await resp.json()
        except Exception as e:
            return {"status": 0, "error": str(e)}
    
    async def get_currencies(self, force_refresh: bool = False) -> dict:
        global _currencies_cache, _currencies_cache_time
        
        now = time.time()
        if _currencies_cache and not force_refresh and (now - _currencies_cache_time) < CACHE_TTL:
            return _currencies_cache
        
        result = await self._request("GET", "/v1/common/currencies")
        
        if result.get("status") == 200:
            _currencies_cache = result.get("data", {})
            _currencies_cache_time = now
            return _currencies_cache
        
        return _currencies_cache or {}
    
    async def get_supported_coins(self) -> list[dict]:
        currencies = await self.get_currencies()
        supported = ["BTC", "ETH", "BNB", "SOL", "USDT", "USDC"]
        
        coins = []
        for symbol in supported:
            if symbol in currencies:
                coin_data = currencies[symbol]
                coins.append({
                    "symbol": symbol,
                    "name": coin_data.get("name", symbol),
                    "networks": coin_data.get("networks", {})
                })
        
        return coins
    
    async def get_coin_networks(self, symbol: str) -> list[dict]:
        currencies = await self.get_currencies()
        
        if symbol not in currencies:
            return []
        
        networks = currencies[symbol].get("networks", {})
        result = []
        
        for network_key, network_data in networks.items():
            result.append({
                "network": network_data.get("network", network_key),
                "name": network_data.get("name", network_key),
                "withdraw_fee": Decimal(str(network_data.get("withdraw_fee", 0))),
                "withdraw_min": Decimal(str(network_data.get("withdraw_min", 0))),
                "deposit_min": Decimal(str(network_data.get("deposit_min", 0))),
            })
        
        return result
    
    async def get_prices(self) -> dict:
        """Get all crypto prices in USD"""
        global _prices_cache, _prices_cache_time
        
        now = time.time()
        if _prices_cache and (now - _prices_cache_time) < CACHE_TTL:
            return _prices_cache
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/v1/common/prices"
        
        try:
            async with session.get(url) as resp:
                result = await resp.json()
                if result.get("status") == 200:
                    _prices_cache = result.get("data", {})
                    _prices_cache_time = now
                    return _prices_cache
        except Exception:
            pass
        return _prices_cache or {}
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> Optional[Decimal]:
        """Get exchange rate for a specific currency to USD"""
        prices = await self.get_prices()
        
        if from_currency in prices:
            rate = prices[from_currency]
            if rate:
                return Decimal(str(rate))
        
        return None
    
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        network: str,
        order_id: str,
        callback_url: str,
        description: Optional[str] = None,
        lifetime: int = 3600
    ) -> PaymentResult:
        data = {
            "amount": float(amount),
            "currency": currency,
            "network": network,
            "orderId": order_id,
            "callbackUrl": callback_url,
            "lifeTime": lifetime,
        }
        
        if description:
            data["description"] = description
        
        result = await self._request("POST", "/v1/payment/create", data)
        
        if result.get("status") == 200:
            payment_data = result.get("data", {})
            return PaymentResult(
                success=True,
                payment_id=payment_data.get("trackId"),
                address=payment_data.get("address"),
            )
        
        return PaymentResult(
            success=False,
            error=result.get("message", "Unknown error")
        )
    
    async def create_static_address(
        self,
        currency: str,
        network: str,
        callback_url: str,
    ) -> PaymentResult:
        data = {
            "network": network,
            "callback_url": callback_url,
        }
        
        result = await self._request("POST", "/v1/payment/static-address", data)
        
        if result.get("status") == 200:
            payment_data = result.get("data", {})
            return PaymentResult(
                success=True,
                payment_id=payment_data.get("track_id"),
                address=payment_data.get("address"),
            )
        
        return PaymentResult(
            success=False,
            error=result.get("message", "Unknown error")
        )
    
    async def create_payout(
        self,
        address: str,
        amount: Decimal,
        currency: str,
        network: str,
        callback_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> PayoutResult:
        data = {
            "address": address,
            "amount": float(amount),
            "currency": currency,
            "network": network,
        }
        
        if callback_url:
            data["callbackUrl"] = callback_url
        
        if description:
            data["description"] = description
        
        result = await self._request("POST", "/v1/payout/create", data, use_payout_key=True)
        
        if result.get("status") == 200:
            payout_data = result.get("data", {})
            return PayoutResult(
                success=True,
                payout_id=payout_data.get("trackId"),
                tx_hash=payout_data.get("txHash"),
            )
        
        return PayoutResult(
            success=False,
            error=result.get("message", "Unknown error")
        )
    
    async def get_payment_status(self, track_id: str) -> dict:
        result = await self._request(
            "POST",
            "/v1/payment/info",
            {"trackId": track_id}
        )
        
        if result.get("status") == 200:
            return result.get("data", {})
        
        return {}
    
    async def get_payout_status(self, track_id: str) -> dict:
        result = await self._request(
            "POST",
            "/v1/payout/info",
            {"trackId": track_id},
            use_payout_key=True
        )
        
        if result.get("status") == 200:
            return result.get("data", {})
        
        return {}
    
    def verify_webhook(self, payload: dict, signature: str) -> bool:
        if not self.webhook_secret:
            return False
        
        sorted_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            sorted_payload.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)
    
    async def get_balance(self, currency: Optional[str] = None, use_payout: bool = True) -> dict:
        data = {}
        if currency:
            data["currency"] = currency
        
        result = await self._request("POST", "/v1/general/balance", data, use_payout_key=use_payout)
        
        if result.get("status") == 200:
            return result.get("data", {})
        
        return {}
