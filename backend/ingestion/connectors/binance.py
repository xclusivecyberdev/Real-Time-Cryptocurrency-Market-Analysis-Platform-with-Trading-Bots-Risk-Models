"""Binance exchange connector."""
import asyncio
import json
from typing import Dict, List, Optional, Callable
from loguru import logger
import ccxt.async_support as ccxt
import websockets

from .base import BaseExchangeConnector


class BinanceConnector(BaseExchangeConnector):
    """Binance exchange connector with WebSocket support."""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        """Initialize Binance connector."""
        super().__init__(api_key, api_secret, testnet)
        self.ws_base_url = "wss://testnet.binance.vision/ws" if testnet else "wss://stream.binance.com:9443/ws"
        self.rest_base_url = "https://testnet.binance.vision/api" if testnet else "https://api.binance.com/api"
        self._ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._ws_tasks: List[asyncio.Task] = []

    async def connect(self) -> bool:
        """Establish connection to Binance."""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }

            if self.testnet:
                config['urls'] = {
                    'api': {
                        'public': self.rest_base_url,
                        'private': self.rest_base_url,
                    }
                }

            self.exchange = ccxt.binance(config)
            await self.exchange.load_markets()
            self._is_connected = True
            logger.info("Connected to Binance")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Binance."""
        # Close all WebSocket connections
        for ws in self._ws_connections.values():
            await ws.close()

        # Cancel all WebSocket tasks
        for task in self._ws_tasks:
            task.cancel()

        if self.exchange:
            await self.exchange.close()

        self._is_connected = False
        logger.info("Disconnected from Binance")

    async def subscribe_ticker(self, symbol: str, callback: Callable) -> None:
        """Subscribe to ticker updates via WebSocket."""
        stream_symbol = symbol.replace('/', '').lower()
        stream = f"{stream_symbol}@ticker"

        async def handle_ticker():
            ws_url = f"{self.ws_base_url}/{stream}"
            async with websockets.connect(ws_url) as websocket:
                self._ws_connections[f"ticker_{symbol}"] = websocket
                logger.info(f"Subscribed to Binance ticker for {symbol}")

                async for message in websocket:
                    data = json.loads(message)
                    ticker = {
                        'symbol': symbol,
                        'exchange': 'binance',
                        'last': float(data.get('c', 0)),
                        'bid': float(data.get('b', 0)),
                        'ask': float(data.get('a', 0)),
                        'high': float(data.get('h', 0)),
                        'low': float(data.get('l', 0)),
                        'volume': float(data.get('v', 0)),
                        'timestamp': data.get('E', 0)
                    }
                    await callback(ticker)

        task = asyncio.create_task(handle_ticker())
        self._ws_tasks.append(task)

    async def subscribe_orderbook(self, symbol: str, callback: Callable, depth: int = 20) -> None:
        """Subscribe to order book updates via WebSocket."""
        stream_symbol = symbol.replace('/', '').lower()
        stream = f"{stream_symbol}@depth{depth}"

        async def handle_orderbook():
            ws_url = f"{self.ws_base_url}/{stream}"
            async with websockets.connect(ws_url) as websocket:
                self._ws_connections[f"orderbook_{symbol}"] = websocket
                logger.info(f"Subscribed to Binance order book for {symbol}")

                async for message in websocket:
                    data = json.loads(message)
                    orderbook = {
                        'symbol': symbol,
                        'exchange': 'binance',
                        'bids': [[float(price), float(amount)] for price, amount in data.get('b', [])],
                        'asks': [[float(price), float(amount)] for price, amount in data.get('a', [])],
                        'timestamp': data.get('E', 0)
                    }
                    await callback(orderbook)

        task = asyncio.create_task(handle_orderbook())
        self._ws_tasks.append(task)

    async def subscribe_trades(self, symbol: str, callback: Callable) -> None:
        """Subscribe to trade updates via WebSocket."""
        stream_symbol = symbol.replace('/', '').lower()
        stream = f"{stream_symbol}@trade"

        async def handle_trades():
            ws_url = f"{self.ws_base_url}/{stream}"
            async with websockets.connect(ws_url) as websocket:
                self._ws_connections[f"trades_{symbol}"] = websocket
                logger.info(f"Subscribed to Binance trades for {symbol}")

                async for message in websocket:
                    data = json.loads(message)
                    trade = {
                        'symbol': symbol,
                        'exchange': 'binance',
                        'id': data.get('t'),
                        'price': float(data.get('p', 0)),
                        'amount': float(data.get('q', 0)),
                        'side': 'buy' if data.get('m') is False else 'sell',
                        'timestamp': data.get('T', 0)
                    }
                    await callback(trade)

        task = asyncio.create_task(handle_trades())
        self._ws_tasks.append(task)

    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[int] = None,
        limit: int = 1000
    ) -> List[List]:
        """Fetch historical OHLCV data."""
        if not self.exchange:
            raise Exception("Not connected to Binance")

        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return []

    async def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Get current funding rate for futures."""
        if not self.exchange:
            raise Exception("Not connected to Binance")

        try:
            # Switch to futures market temporarily
            self.exchange.options['defaultType'] = 'future'
            funding_rate = await self.exchange.fetch_funding_rate(symbol)
            self.exchange.options['defaultType'] = 'spot'
            return funding_rate
        except Exception as e:
            logger.error(f"Failed to fetch funding rate for {symbol}: {e}")
            self.exchange.options['defaultType'] = 'spot'
            return None

    async def subscribe_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ) -> None:
        """Subscribe to candlestick/kline updates."""
        stream_symbol = symbol.replace('/', '').lower()
        stream = f"{stream_symbol}@kline_{interval}"

        async def handle_klines():
            ws_url = f"{self.ws_base_url}/{stream}"
            async with websockets.connect(ws_url) as websocket:
                self._ws_connections[f"klines_{symbol}_{interval}"] = websocket
                logger.info(f"Subscribed to Binance klines for {symbol} ({interval})")

                async for message in websocket:
                    data = json.loads(message)
                    k = data.get('k', {})
                    kline = {
                        'symbol': symbol,
                        'exchange': 'binance',
                        'interval': interval,
                        'timestamp': k.get('t'),
                        'open': float(k.get('o', 0)),
                        'high': float(k.get('h', 0)),
                        'low': float(k.get('l', 0)),
                        'close': float(k.get('c', 0)),
                        'volume': float(k.get('v', 0)),
                        'closed': k.get('x', False)
                    }
                    await callback(kline)

        task = asyncio.create_task(handle_klines())
        self._ws_tasks.append(task)
