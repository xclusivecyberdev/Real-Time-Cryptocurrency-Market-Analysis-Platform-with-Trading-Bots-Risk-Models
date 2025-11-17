"""Mean reversion trading strategy."""
import numpy as np
import pandas as pd
from typing import Dict, Any
from loguru import logger

from .base import BaseStrategy, TradingSignal, SignalType
from backend.analytics.indicators import TechnicalIndicators


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy.

    Assumes prices revert to their mean. Buys when price is significantly
    below mean, sells when significantly above mean.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mean reversion strategy.

        Config parameters:
            - lookback_period: Period for calculating mean (default: 20)
            - entry_threshold: Z-score threshold for entry (default: 2.0)
            - exit_threshold: Z-score threshold for exit (default: 0.5)
            - use_bollinger: Use Bollinger Bands instead of z-score (default: False)
            - stop_loss_percent: Stop loss percentage (default: 5)
        """
        super().__init__(config)

        self.lookback_period = config.get('lookback_period', 20)
        self.entry_threshold = config.get('entry_threshold', 2.0)
        self.exit_threshold = config.get('exit_threshold', 0.5)
        self.use_bollinger = config.get('use_bollinger', False)
        self.stop_loss_percent = config.get('stop_loss_percent', 5)

    def calculate_z_score(self, data: pd.DataFrame) -> float:
        """
        Calculate z-score of current price.

        Args:
            data: Market data

        Returns:
            Z-score
        """
        prices = data['close'].values
        current_price = prices[-1]

        mean = np.mean(prices[-self.lookback_period:])
        std = np.std(prices[-self.lookback_period:])

        if std == 0:
            return 0

        z_score = (current_price - mean) / std
        return z_score

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """Generate mean reversion signal."""
        current_price = data['close'].iloc[-1]

        if self.use_bollinger:
            # Use Bollinger Bands
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
                data['close'].values,
                period=self.lookback_period
            )

            current_upper = upper[-1]
            current_middle = middle[-1]
            current_lower = lower[-1]

            # Calculate position within bands
            if current_upper != current_lower:
                position = (current_price - current_lower) / (current_upper - current_lower)
            else:
                position = 0.5

            # Buy when price touches lower band
            if position < 0.1 and self.position == 0:
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    price=current_price,
                    confidence=1.0,
                    reason=f"Price at lower Bollinger Band ({current_price:.2f} < {current_lower:.2f})"
                )

            # Sell when price touches upper band or reverts to mean
            elif (position > 0.9 or position > 0.5) and self.position > 0:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=1.0 if position > 0.9 else 0.7,
                    reason=f"Price at upper band or mean reversion ({current_price:.2f})"
                )

        else:
            # Use z-score
            z_score = self.calculate_z_score(data)

            # Buy when price is significantly below mean (oversold)
            if z_score < -self.entry_threshold and self.position == 0:
                return TradingSignal(
                    signal_type=SignalType.BUY,
                    price=current_price,
                    confidence=min(abs(z_score) / self.entry_threshold, 1.0),
                    reason=f"Price below mean (z-score: {z_score:.2f})",
                    metadata={'z_score': z_score}
                )

            # Sell when price is significantly above mean (overbought)
            elif z_score > self.entry_threshold and self.position == 0:
                # Short signal (not implemented for spot trading)
                pass

            # Exit long when price reverts to mean
            elif abs(z_score) < self.exit_threshold and self.position > 0:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=1.0,
                    reason=f"Mean reversion (z-score: {z_score:.2f})",
                    metadata={'z_score': z_score}
                )

        # Check stop loss
        if self.position > 0 and self.entry_price > 0:
            loss_percent = ((current_price - self.entry_price) / self.entry_price) * 100

            if loss_percent < -self.stop_loss_percent:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=1.0,
                    reason=f"Stop loss triggered ({loss_percent:.2f}%)",
                    metadata={'stop_loss': True}
                )

        return TradingSignal(
            signal_type=SignalType.HOLD,
            price=current_price,
            reason="No mean reversion signal"
        )

    def should_enter(self, data: pd.DataFrame) -> bool:
        """Check if should enter position."""
        if self.position > 0:
            return False

        z_score = self.calculate_z_score(data)
        return abs(z_score) >= self.entry_threshold

    def should_exit(self, data: pd.DataFrame) -> bool:
        """Check if should exit position."""
        if self.position == 0:
            return False

        z_score = self.calculate_z_score(data)

        # Exit on mean reversion
        if abs(z_score) < self.exit_threshold:
            return True

        # Exit on stop loss
        current_price = data['close'].iloc[-1]
        if self.entry_price > 0:
            loss_percent = ((current_price - self.entry_price) / self.entry_price) * 100
            if loss_percent < -self.stop_loss_percent:
                return True

        return False
