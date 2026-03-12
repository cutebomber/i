"""
OxaPay Payment Monitor
-----------------------
Polls pending OxaPay invoices every 20 seconds.
Mirrors ton_monitor.py — runs in the same async loop.
No webhook / public URL needed.

Flow:
  1. User taps "Pay with OxaPay" → bot creates invoice → stores in DB
  2. This monitor wakes every 20s, checks all pending invoices via OxaPay API
  3. If status == "Paid" → credit user balance, notify them, mark invoice done
"""

import asyncio
import logging
import httpx
import database as db
from config import OXAPAY_MERCHANT_KEY, TON_PRICE_USD

logger = logging.getLogger(__name__)

OXAPAY_API    = "https://api.oxapay.com"
POLL_INTERVAL = 20   # seconds between checks


async def create_invoice_async(telegram_id: int, amount_usd: float) -> dict:
    """
    Create an OxaPay static invoice for a given USD amount.
    Stores it as pending in DB so the monitor picks it up.
    Returns dict with 'success', 'pay_link', 'track_id'.
    """
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "merchant":     OXAPAY_MERCHANT_KEY,
                "amount":       amount_usd,
                "currency":     "USD",
                "lifeTime":     30,         # 30 minutes to pay
                "feePaidByPayer": 1,         # buyer covers network fee
                "description":  f"Balance top-up for user {telegram_id}",
                "orderId":      str(telegram_id),
            }
            resp = await client.post(
                f"{OXAPAY_API}/merchants/request",
                json=payload,
                timeout=15
            )
            data = resp.json()

        if data.get("result") == 100:
            track_id = data.get("trackId", "")
            pay_link = data.get("payLink", "")
            db.create_oxapay_invoice(telegram_id, track_id, amount_usd)
            return {"success": True, "pay_link": pay_link, "track_id": track_id}
        else:
            logger.warning(f"OxaPay create error: {data}")
            return {"success": False, "error": data.get("message", "Unknown error")}

    except Exception as e:
        logger.error(f"OxaPay create_invoice_async error: {e}")
        return {"success": False, "error": str(e)}


async def check_invoice(client: httpx.AsyncClient, invoice: dict, bot) -> bool:
    """
    Query OxaPay for one invoice status.
    Returns True if payment was just confirmed and processed.
    """
    track_id = invoice["track_id"]
    try:
        resp = await client.post(
            f"{OXAPAY_API}/merchants/inquiry",
            json={"merchant": OXAPAY_MERCHANT_KEY, "trackId": track_id},
            timeout=15
        )
        data = resp.json()
    except Exception as e:
        logger.error(f"OxaPay inquiry error ({track_id}): {e}")
        return False

    result = data.get("result")
    status = data.get("status", "")

    # result 100 + status "Paid" = confirmed
    if result == 100 and status == "Paid":
        paid_invoice = db.mark_oxapay_paid(track_id)
        if not paid_invoice:
            # Already processed (race guard)
            return False

        telegram_id = paid_invoice["telegram_id"]
        amount_usd  = paid_invoice["amount_usd"]

        # Convert USD → TON and credit
        ton_amount  = round(amount_usd / TON_PRICE_USD, 6)
        db.add_balance(telegram_id, ton_amount)
        db.record_transaction(telegram_id, ton_amount, f"oxapay_{track_id}")

        price        = db.get_price_ton()
        new_balance  = db.get_balance(telegram_id)
        can_buy      = int(new_balance // price) if price > 0 else 0

        logger.info(f"OxaPay: credited {ton_amount:.4f} TON to {telegram_id} (${amount_usd})")

        try:
            bot.send_message(
                telegram_id,
                f"✅ <b>Balance Added via OxaPay!</b>\n\n"
                f"💵 Paid: <b>${amount_usd:.2f}</b>\n"
                f"🪙 Credited: <b>{ton_amount:.4f} TON</b>\n"
                f"💳 New Balance: <b>{new_balance:.4f} TON</b>\n"
                f"🛒 You can buy: <b>{can_buy} account(s)</b>\n\n"
                f"Use 🛒 <b>Buy Account</b> to purchase!",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify user {telegram_id}: {e}")

        return True

    # Mark expired invoices so we stop polling them
    if status in ("Expired", "Failed", "Cancelled"):
        db.expire_oxapay_invoice(track_id)
        logger.info(f"OxaPay invoice {track_id} marked {status}")

    return False


async def start_monitoring(bot):
    """
    Main polling loop. Checks all pending OxaPay invoices every POLL_INTERVAL seconds.
    Called from bot.py startup the same way ton_monitor.start_monitoring is called.
    """
    logger.info("OxaPay monitor started.")
    async with httpx.AsyncClient() as client:
        while True:
            try:
                pending = db.get_pending_oxapay_invoices()
                if pending:
                    logger.debug(f"Checking {len(pending)} pending OxaPay invoice(s)...")
                    for invoice in pending:
                        await check_invoice(client, invoice, bot)
            except Exception as e:
                logger.error(f"OxaPay monitor loop error: {e}")

            await asyncio.sleep(POLL_INTERVAL)
