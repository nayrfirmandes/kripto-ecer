import aiohttp
from decimal import Decimal
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class InvoiceResult:
    success: bool
    invoice_id: Optional[str] = None
    pay_url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExchangeRate:
    source: str
    target: str
    rate: Decimal
    is_valid: bool


class CryptoBotService:
    BASE_URL = "https://pay.crypt.bot/api"
    SUPPORTED_COINS = ["USDT", "USDC"]
    USD_TO_IDR = Decimal("16000")
    
    def __init__(self, api_token: str, margin: float = 0.05):
        self.api_token = api_token
        self.margin = margin
        self._session: Optional[aiohttp.ClientSession] = None
        self._rates_cache: Dict[str, ExchangeRate] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(self, method: str, data: Optional[dict] = None) -> dict:
        session = await self._get_session()
        url = f"{self.BASE_URL}/{method}"
        
        headers = {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json",
        }
        
        try:
            async with session.post(url, json=data or {}, headers=headers) as resp:
                return await resp.json()
        except Exception as e:
            return {"ok": False, "error": {"code": 0, "name": str(e)}}
    
    async def get_me(self) -> dict:
        result = await self._request("getMe")
        if result.get("ok"):
            return result.get("result", {})
        return {}
    
    async def get_exchange_rates(self) -> Dict[str, ExchangeRate]:
        result = await self._request("getExchangeRates")
        rates = {}
        
        if result.get("ok"):
            for item in result.get("result", []):
                if item.get("target") == "USD":
                    source = item.get("source", "")
                    rates[source] = ExchangeRate(
                        source=source,
                        target="USD",
                        rate=Decimal(str(item.get("rate", "1"))),
                        is_valid=item.get("is_valid", False),
                    )
        
        self._rates_cache = rates
        return rates
    
    async def get_usd_rate(self, asset: str) -> Decimal:
        if not self._rates_cache:
            await self.get_exchange_rates()
        
        rate = self._rates_cache.get(asset)
        if rate and rate.is_valid:
            return rate.rate
        return Decimal("1")
    
    async def get_idr_rate(self, asset: str) -> Decimal:
        usd_rate = await self.get_usd_rate(asset)
        return usd_rate * self.USD_TO_IDR
    
    async def create_invoice(
        self,
        asset: str,
        amount: Decimal,
        description: Optional[str] = None,
        expires_in: int = 3600,
    ) -> InvoiceResult:
        if asset not in self.SUPPORTED_COINS:
            return InvoiceResult(
                success=False,
                error=f"Asset {asset} tidak didukung. Hanya USDT dan USDC."
            )
        
        amount_with_margin = amount * Decimal(str(1 + self.margin))
        
        data = {
            "asset": asset,
            "amount": str(amount_with_margin.quantize(Decimal("0.01"))),
            "expires_in": expires_in,
        }
        
        if description:
            data["description"] = description
        
        result = await self._request("createInvoice", data)
        
        if result.get("ok"):
            invoice = result.get("result", {})
            return InvoiceResult(
                success=True,
                invoice_id=str(invoice.get("invoice_id")),
                pay_url=invoice.get("pay_url"),
            )
        
        error = result.get("error", {})
        return InvoiceResult(
            success=False,
            error=error.get("name", "Unknown error")
        )
    
    async def get_invoice(self, invoice_id: str) -> dict:
        result = await self._request("getInvoices", {"invoice_ids": [int(invoice_id)]})
        if result.get("ok"):
            items = result.get("result", {}).get("items", [])
            if items:
                return items[0]
        return {}
    
    def calculate_deposit_amount(self, crypto_amount: Decimal) -> Decimal:
        return crypto_amount / Decimal(str(1 + self.margin))
