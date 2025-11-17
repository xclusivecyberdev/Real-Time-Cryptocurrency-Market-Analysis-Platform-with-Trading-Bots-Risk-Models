"""Market data API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class MarketTicker(BaseModel):
    """Market ticker model."""
    symbol: str
    exchange: str
    last: float
    bid: float
    ask: float
    volume: float
    change_24h: float
    timestamp: datetime


class OHLCV(BaseModel):
    """OHLCV candlestick model."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@router.get("/ticker/{exchange}/{symbol}")
async def get_ticker(exchange: str, symbol: str):
    """Get current ticker for a symbol."""
    # Mock data - in production, fetch from exchange connector
    return {
        "symbol": symbol,
        "exchange": exchange,
        "last": 50000.0,
        "bid": 49995.0,
        "ask": 50005.0,
        "volume": 1234567.0,
        "change_24h": 2.5,
        "timestamp": datetime.utcnow()
    }


@router.get("/ohlcv/{exchange}/{symbol}")
async def get_ohlcv(
    exchange: str,
    symbol: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get OHLCV candlestick data."""
    # Mock data - in production, fetch from database
    return {
        "exchange": exchange,
        "symbol": symbol,
        "timeframe": timeframe,
        "data": [
            {
                "timestamp": datetime.utcnow(),
                "open": 50000,
                "high": 50500,
                "low": 49500,
                "close": 50200,
                "volume": 123.45
            }
        ]
    }


@router.get("/exchanges")
async def get_supported_exchanges():
    """Get list of supported exchanges."""
    return {
        "exchanges": ["binance", "bybit", "coinbase", "kraken", "kucoin"]
    }


@router.get("/symbols/{exchange}")
async def get_symbols(exchange: str):
    """Get available trading symbols for an exchange."""
    return {
        "exchange": exchange,
        "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
    }
