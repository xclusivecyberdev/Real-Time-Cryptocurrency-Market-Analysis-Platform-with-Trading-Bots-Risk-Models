"""Factory for creating exchange connectors."""
from typing import Dict, Optional
from .base import BaseExchangeConnector
from .binance import BinanceConnector
import ccxt.async_support as ccxt
from loguru import logger


class GenericCCXTConnector(BaseExchangeConnector):
    """Generic CCXT connector for exchanges without custom WebSocket implementation."""

    def __init__(
        self,
        exchange_id: str,
        api_key: str = "",
        api_secret: str = "",
        password: str = "",
        testnet: bool = True
    ):
        """Initialize generic CCXT connector."""
        super().__init__(api_key, api_secret, testnet)
        self.exchange_id = exchange_id
        self.password = password

    async def connect(self) -> bool:
        """Establish connection to exchange."""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            }

            if self.password:
                config['password'] = self.password

            if self.testnet and hasattr(exchange_class, 'set_sandbox_mode'):
                config['options'] = {'sandboxMode': True}

            self.exchange = exchange_class(config)
            await self.exchange.load_markets()
            self._is_connected = True
            logger.info(f"Connected to {self.exchange_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from exchange."""
        if self.exchange:
            await self.exchange.close()
        self._is_connected = False
        logger.info(f"Disconnected from {self.exchange_id}")

    async def subscribe_ticker(self, symbol: str, callback) -> None:
        """Subscribe to ticker (polling-based for generic connector)."""
        logger.warning(f"{self.exchange_id}: WebSocket not implemented, using polling")
        # Implement polling fallback if needed

    async def subscribe_orderbook(self, symbol: str, callback) -> None:
        """Subscribe to order book (polling-based for generic connector)."""
        logger.warning(f"{self.exchange_id}: WebSocket not implemented, using polling")

    async def subscribe_trades(self, symbol: str, callback) -> None:
        """Subscribe to trades (polling-based for generic connector)."""
        logger.warning(f"{self.exchange_id}: WebSocket not implemented, using polling")

    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[int] = None,
        limit: int = 1000
    ):
        """Fetch historical OHLCV data."""
        if not self.exchange:
            raise Exception(f"Not connected to {self.exchange_id}")

        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol} on {self.exchange_id}: {e}")
            return []

    async def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Get current funding rate."""
        if not self.exchange or not hasattr(self.exchange, 'fetch_funding_rate'):
            return None

        try:
            return await self.exchange.fetch_funding_rate(symbol)
        except Exception as e:
            logger.error(f"Failed to fetch funding rate for {symbol} on {self.exchange_id}: {e}")
            return None


class ExchangeConnectorFactory:
    """Factory for creating exchange connectors."""

    @staticmethod
    def create(
        exchange: str,
        api_key: str = "",
        api_secret: str = "",
        password: str = "",
        testnet: bool = True
    ) -> BaseExchangeConnector:
        """Create an exchange connector instance."""
        exchange = exchange.lower()

        # Use custom connector for Binance (has WebSocket implementation)
        if exchange == 'binance':
            return BinanceConnector(api_key, api_secret, testnet)

        # For other exchanges, use generic CCXT connector
        # In production, you'd implement custom WebSocket connectors for each
        elif exchange in ['bybit', 'coinbase', 'kraken', 'kucoin']:
            return GenericCCXTConnector(
                exchange_id=exchange,
                api_key=api_key,
                api_secret=api_secret,
                password=password,
                testnet=testnet
            )

        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    @staticmethod
    def get_supported_exchanges():
        """Get list of supported exchanges."""
        return ['binance', 'bybit', 'coinbase', 'kraken', 'kucoin']
