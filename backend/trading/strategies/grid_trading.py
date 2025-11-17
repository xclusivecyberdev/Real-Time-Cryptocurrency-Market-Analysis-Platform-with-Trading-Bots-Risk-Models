"""Grid trading strategy implementation."""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from loguru import logger

from .base import BaseStrategy, TradingSignal, SignalType


class GridTradingStrategy(BaseStrategy):
    """
    Grid trading strategy.

    Places buy and sell orders at regular intervals (grid levels)
    around a base price. Profits from market volatility.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize grid trading strategy.

        Config parameters:
            - grid_levels: Number of grid levels (default: 10)
            - price_range_percent: Price range as % of base price (default: 10)
            - grid_spacing: Spacing between grid levels ('arithmetic' or 'geometric')
            - investment_per_grid: Amount to invest per grid level
            - base_price: Base price for grid (optional, will use current price if not set)
        """
        super().__init__(config)

        self.grid_levels = config.get('grid_levels', 10)
        self.price_range_percent = config.get('price_range_percent', 10)
        self.grid_spacing = config.get('grid_spacing', 'arithmetic')
        self.investment_per_grid = config.get('investment_per_grid', 100)
        self.base_price = config.get('base_price', None)

        self.grid_buy_prices: List[float] = []
        self.grid_sell_prices: List[float] = []
        self.grid_orders: Dict[float, Dict] = {}
        self.initialized = False

    def initialize_grid(self, current_price: float):
        """
        Initialize grid levels.

        Args:
            current_price: Current market price
        """
        if self.base_price is None:
            self.base_price = current_price

        price_range = self.base_price * (self.price_range_percent / 100)
        lower_bound = self.base_price - price_range
        upper_bound = self.base_price + price_range

        half_levels = self.grid_levels // 2

        if self.grid_spacing == 'arithmetic':
            # Equal spacing
            self.grid_buy_prices = np.linspace(lower_bound, self.base_price, half_levels + 1)[:-1].tolist()
            self.grid_sell_prices = np.linspace(self.base_price, upper_bound, half_levels + 1)[1:].tolist()
        else:  # geometric
            # Logarithmic spacing
            self.grid_buy_prices = np.geomspace(lower_bound, self.base_price, half_levels + 1)[:-1].tolist()
            self.grid_sell_prices = np.geomspace(self.base_price, upper_bound, half_levels + 1)[1:].tolist()

        # Initialize grid orders
        for price in self.grid_buy_prices:
            self.grid_orders[price] = {'type': 'buy', 'filled': False}

        for price in self.grid_sell_prices:
            self.grid_orders[price] = {'type': 'sell', 'filled': False}

        self.initialized = True
        logger.info(f"Grid initialized with {self.grid_levels} levels around {self.base_price}")
        logger.info(f"Buy levels: {self.grid_buy_prices}")
        logger.info(f"Sell levels: {self.grid_sell_prices}")

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """Generate grid trading signal."""
        current_price = data['close'].iloc[-1]

        if not self.initialized:
            self.initialize_grid(current_price)

        # Check if current price crosses any grid level
        for grid_price, order_info in self.grid_orders.items():
            if order_info['filled']:
                continue

            if order_info['type'] == 'buy' and current_price <= grid_price:
                # Buy signal
                amount = self.investment_per_grid / grid_price
                order_info['filled'] = True

                return TradingSignal(
                    signal_type=SignalType.BUY,
                    price=current_price,
                    amount=amount,
                    confidence=1.0,
                    reason=f"Grid buy at {grid_price}",
                    metadata={'grid_price': grid_price, 'grid_type': 'buy'}
                )

            elif order_info['type'] == 'sell' and current_price >= grid_price:
                # Sell signal
                amount = self.investment_per_grid / self.base_price

                # Only sell if we have position
                if self.position > 0:
                    order_info['filled'] = True

                    return TradingSignal(
                        signal_type=SignalType.SELL,
                        price=current_price,
                        amount=min(amount, self.position),
                        confidence=1.0,
                        reason=f"Grid sell at {grid_price}",
                        metadata={'grid_price': grid_price, 'grid_type': 'sell'}
                    )

        return TradingSignal(
            signal_type=SignalType.HOLD,
            price=current_price,
            reason="No grid level crossed"
        )

    def should_enter(self, data: pd.DataFrame) -> bool:
        """Check if should enter position (grid always ready to enter)."""
        return True

    def should_exit(self, data: pd.DataFrame) -> bool:
        """Check if should exit position (grid exits at sell levels)."""
        current_price = data['close'].iloc[-1]

        # Exit if price crosses sell grid level
        for grid_price in self.grid_sell_prices:
            if current_price >= grid_price and not self.grid_orders[grid_price]['filled']:
                return True

        return False

    def rebalance_grid(self, current_price: float):
        """
        Rebalance grid if price moves significantly from base.

        Args:
            current_price: Current market price
        """
        deviation = abs(current_price - self.base_price) / self.base_price

        # Rebalance if price moved more than 20%
        if deviation > 0.20:
            logger.info(f"Rebalancing grid. Price moved from {self.base_price} to {current_price}")
            self.base_price = current_price
            self.initialized = False
            self.grid_orders = {}

    def reset_filled_orders(self):
        """Reset filled orders (for continuous grid operation)."""
        for price in self.grid_orders:
            self.grid_orders[price]['filled'] = False
