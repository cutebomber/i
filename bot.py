"""
Price Feed
----------
Fetches live TON/USD rate from CoinGecko (free, no API key needed).
Updates every 5 minutes in the background.
Falls back to config.TON_PRICE_USD if the API is unreachable.

Usage anywhere in the bot:
    import price_feed
    rate = price_feed.get_ton_price_usdt()   # e.g. 3.21
    usdt = price_feed.ton_to_usdt(2.5)       # 2.5 TON -> $X USDT
    ton  = price_feed.usdt_to_ton(5.0)       # $5 USDT -> X TON
"""

import asyncio
import logging
import httpx
from config import TON_PRICE_USD

logger = logging.getLogger(__name__)

# In-memory cache
_cached_rate: float = TON_PRICE_USD   # fallback from config
_last_updated: str  = "never"

COINGECKO_URL   = "https://api.coingecko.com/api/v3/simple/price"
UPDATE_INTERVAL = 300   # 5 minutes


def get_ton_price_usdt() -> float:
    """Return the latest cached TON/USD rate."""
    return _cached_rate


def ton_to_usdt(ton_amount: float) -> float:
    """Convert TON amount to USDT at current live rate."""
    return round(ton_amount * _cached_rate, 4)


def usdt_to_ton(usdt_amount: float) -> float:
    """Convert USDT amount to TON at current live rate."""
    if _cached_rate <= 0:
        return 0.0
    return round(usdt_amount / _cached_rate, 6)


def get_last_updated() -> str:
    return _last_updated


async def _fetch_rate(client: httpx.AsyncClient) -> float | None:
    try:
        resp = await client.get(
            COINGECKO_URL,
            params={"ids": "the-open-network", "vs_currencies": "usd"},
            timeout=10
        )
        data = resp.json()
        rate = data["the-open-network"]["usd"]
        return float(rate)
    except Exception as e:
        logger.warning(f"Price feed fetch failed: {e}")
        return None


async def start_price_feed():
    """
    Background loop — updates TON/USD rate every 5 minutes.
    Start it in bot.py alongside ton_monitor:
        asyncio.run_coroutine_threadsafe(price_feed.start_price_feed(), telethon_loop)
    """
    global _cached_rate, _last_updated
    from datetime import datetime

    logger.info("Price feed started (CoinGecko, updates every 5 min)")

    async with httpx.AsyncClient() as client:
        while True:
            rate = await _fetch_rate(client)
            if rate and rate > 0:
                _cached_rate  = rate
                _last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"TON rate updated: ${_cached_rate:.4f} USDT")
            else:
                logger.warning(f"Using cached/fallback TON rate: ${_cached_rate:.4f}")

            await asyncio.sleep(UPDATE_INTERVAL)
