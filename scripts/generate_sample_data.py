#!/usr/bin/env python3
"""Generate sample market data for testing and development."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def generate_ohlcv_data(
    symbol: str = "BTC/USDT",
    start_date: str = "2023-01-01",
    end_date: str = "2023-12-31",
    interval: str = "1h",
    initial_price: float = 40000
):
    """Generate synthetic OHLCV data."""

    # Parse dates
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Generate datetime range
    freq_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1H",
        "4h": "4H",
        "1d": "1D"
    }

    dates = pd.date_range(start=start, end=end, freq=freq_map[interval])

    # Generate price data with random walk
    np.random.seed(42)
    n = len(dates)

    # Generate returns
    returns = np.random.normal(0.0001, 0.02, n)

    # Calculate prices
    prices = initial_price * np.exp(np.cumsum(returns))

    # Generate OHLCV
    data = []
    for i, date in enumerate(dates):
        price = prices[i]

        # Generate high, low within reasonable range
        volatility = price * 0.01  # 1% volatility
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))

        # Open close
        open_price = prices[i-1] if i > 0 else price
        close = price

        # Volume
        volume = abs(np.random.normal(100, 20))

        data.append({
            "timestamp": date.isoformat(),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": round(volume, 2)
        })

    return pd.DataFrame(data)


def generate_orderbook_snapshot():
    """Generate sample order book snapshot."""

    mid_price = 50000

    bids = []
    asks = []

    for i in range(20):
        # Bids (buy orders)
        bid_price = mid_price - (i * 10) - np.random.uniform(0, 10)
        bid_amount = np.random.uniform(0.1, 5.0)
        bids.append([round(bid_price, 2), round(bid_amount, 4)])

        # Asks (sell orders)
        ask_price = mid_price + (i * 10) + np.random.uniform(0, 10)
        ask_amount = np.random.uniform(0.1, 5.0)
        asks.append([round(ask_price, 2), round(ask_amount, 4)])

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "bids": bids,
        "asks": asks
    }


def generate_trades():
    """Generate sample trade data."""

    trades = []
    base_price = 50000

    for i in range(100):
        timestamp = datetime.utcnow() - timedelta(minutes=i)
        price = base_price + np.random.normal(0, 100)
        amount = abs(np.random.normal(0.5, 0.2))
        side = "buy" if np.random.random() > 0.5 else "sell"

        trades.append({
            "timestamp": timestamp.isoformat(),
            "trade_id": f"trade_{i}",
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "side": side,
            "price": round(price, 2),
            "amount": round(amount, 4)
        })

    return trades


def main():
    """Generate all sample data."""

    print("🎲 Generating sample market data...")

    # Create output directory
    os.makedirs("sample_data", exist_ok=True)

    # Generate OHLCV data for multiple symbols
    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
    initial_prices = [40000, 2500, 300, 100]

    for symbol, initial_price in zip(symbols, initial_prices):
        print(f"  Generating OHLCV for {symbol}...")

        # 1-hour data
        df_1h = generate_ohlcv_data(
            symbol=symbol,
            interval="1h",
            initial_price=initial_price
        )
        df_1h.to_csv(f"sample_data/{symbol.replace('/', '_')}_1h.csv", index=False)

        # 1-day data
        df_1d = generate_ohlcv_data(
            symbol=symbol,
            interval="1d",
            initial_price=initial_price
        )
        df_1d.to_csv(f"sample_data/{symbol.replace('/', '_')}_1d.csv", index=False)

    # Generate order book
    print("  Generating order book snapshot...")
    orderbook = generate_orderbook_snapshot()
    with open("sample_data/orderbook_snapshot.json", "w") as f:
        json.dump(orderbook, f, indent=2)

    # Generate trades
    print("  Generating trade data...")
    trades = generate_trades()
    with open("sample_data/trades.json", "w") as f:
        json.dump(trades, f, indent=2)

    print("✅ Sample data generated successfully!")
    print(f"   Location: sample_data/")
    print(f"   Files created:")
    for file in os.listdir("sample_data"):
        print(f"     - {file}")


if __name__ == "__main__":
    main()
