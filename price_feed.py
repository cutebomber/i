"""
Price Feed — Live TON/USDT
---------------------------
Fetches TON price in USDT from CoinGecko every 5 minutes.
Falls back to last known price if the request fails.
No API key required.

Usage anywhere in the bot:
    from price_feed import get_ton_price_usdt, ton_to_usdt, usdt_to_ton
"""

import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

# ── Cache ──────────────────────────────────────────────
_cached_price: float = 3.0        # fallback until first fetch
_last_fetched: float = 0.0
REFRESH_INTERVAL    = 300          # 5 minutes

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=the-open-network&vs_currencies=usdt"
)


async def _fetch_price() -> float:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(COINGECKO_URL, timeout=10)
            data = resp.json()
            price = float(data["the-open-network"]["usdt"])
            logger.info(f"TON price updated: ${price:.4f} USDT")
            return price
    except Exception as e:
        logger.warning(f"Price fetch failed: {e} — using cached ${_cached_price:.4f}")
        return _cached_price


def get_ton_price_usdt() -> float:
    """Return cached TON/USDT price (always safe to call synchronously)."""
    return _cached_price


def ton_to_usdt(ton: float) -> float:
    """Convert TON amount to USDT using live price."""
    return round(ton * _cached_price, 4)


def usdt_to_ton(usdt: float) -> float:
    """Convert USDT amount to TON using live price."""
    if _cached_price <= 0:
        return 0.0
    return round(usdt / _cached_price, 6)


async def start_price_feed():
    """
    Refresh loop — runs forever in the async event loop.
    Call once at startup alongside ton_monitor and oxapay_monitor.
    """
    global _cached_price, _last_fetched
    import time

    logger.info("Price feed started.")
    while True:
        price = await _fetch_price()
        if price > 0:
            _cached_price = price
            _last_fetched = time.time()
        await asyncio.sleep(REFRESH_INTERVAL)
