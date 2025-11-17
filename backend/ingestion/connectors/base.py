"""Base connector interface for exchange integrations."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import asyncio
import ccxt.async_support as ccxt


class BaseExchangeConnector(ABC):
    """Base class for exchange connectors."""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        """Initialize connector."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange: Optional[ccxt.Exchange] = None
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to exchange."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from exchange."""
        pass

    @abstractmethod
    async def subscribe_ticker(self, symbol: str, callback: Callable) -> None:
        """Subscribe to ticker updates."""
        pass

    @abstractmethod
    async def subscribe_orderbook(self, symbol: str, callback: Callable) -> None:
        """Subscribe to order book updates."""
        pass

    @abstractmethod
    async def subscribe_trades(self, symbol: str, callback: Callable) -> None:
        """Subscribe to trade updates."""
        pass

    @abstractmethod
    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[int] = None,
        limit: int = 1000
    ) -> List[List]:
        """Fetch historical OHLCV data."""
        pass

    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Get current funding rate (for futures)."""
        pass

    async def get_markets(self) -> Dict:
        """Get available markets."""
        if not self.exchange:
            raise Exception("Not connected to exchange")
        return await self.exchange.load_markets()

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker."""
        if not self.exchange:
            raise Exception("Not connected to exchange")
        return await self.exchange.fetch_ticker(symbol)

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book snapshot."""
        if not self.exchange:
            raise Exception("Not connected to exchange")
        return await self.exchange.fetch_order_book(symbol, limit)

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades."""
        if not self.exchange:
            raise Exception("Not connected to exchange")
        return await self.exchange.fetch_trades(symbol, limit=limit)

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._is_connected

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
