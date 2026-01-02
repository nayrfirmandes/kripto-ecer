import logging
import json
from decimal import Decimal
from aiohttp import web
from prisma import Prisma

from bot.services.oxapay import OxaPayService
from bot.db.queries import update_balance
from bot.config import config

logger = logging.getLogger(__name__)


async def handle_oxapay_webhook(request: web.Request) -> web.Response:
    try:
        signature = request.headers.get("X-OxaPay-Signature", "")
        body = await request.json()
        
        logger.info(f"Received webhook: {json.dumps(body)}")
        
        oxapay = OxaPayService(
            merchant_api_key=config.oxapay.merchant_api_key,
            payout_api_key=config.oxapay.payout_api_key,
            webhook_secret=config.oxapay.webhook_secret,
        )
        
        if config.oxapay.webhook_secret and signature:
            if not oxapay.verify_webhook(body, signature):
                logger.warning("Invalid webhook signature")
                return web.json_response({"error": "Invalid signature"}, status=401)
        
        status = body.get("status")
        track_id = body.get("trackId")
        order_id = body.get("orderId", "")
        
        if not track_id:
            return web.json_response({"error": "Missing trackId"}, status=400)
        
        db: Prisma = request.app["db"]
        
        if order_id.startswith("SELL_"):
            order = await db.cryptoorder.find_first(
                where={"oxapayPaymentId": track_id},
                include={"user": True}
            )
            
            if order and status == "Paid":
                await db.cryptoorder.update(
                    where={"id": order.id},
                    data={"status": "COMPLETED"}
                )
                
                await update_balance(db, order.userId, order.fiatAmount)
                
                await db.transaction.create(
                    data={
                        "userId": order.userId,
                        "type": "SELL",
                        "amount": order.fiatAmount,
                        "status": "COMPLETED",
                        "description": f"Jual {order.cryptoAmount} {order.coinSymbol}",
                        "metadata": {"orderId": order.id},
                    }
                )
                
                logger.info(f"Sell order {order.id} completed, added {order.fiatAmount} to balance")
        
        return web.json_response({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return web.json_response({"error": str(e)}, status=500)


async def health_check(request: web.Request) -> web.Response:
    return web.json_response({"status": "healthy"})


async def create_webhook_app(db: Prisma) -> web.Application:
    app = web.Application()
    app["db"] = db
    
    app.router.add_post("/webhook/oxapay", handle_oxapay_webhook)
    app.router.add_get("/health", health_check)
    
    return app


async def run_webhook_server(db: Prisma, host: str = "0.0.0.0", port: int = 8080):
    app = await create_webhook_app(db)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Webhook server running on {host}:{port}")
    return runner
