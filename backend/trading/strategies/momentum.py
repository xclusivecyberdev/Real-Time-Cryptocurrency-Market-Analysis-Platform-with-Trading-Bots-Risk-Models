"""Momentum trading strategy."""
import numpy as np
import pandas as pd
from typing import Dict, Any
from loguru import logger

from .base import BaseStrategy, TradingSignal, SignalType
from backend.analytics.indicators import TechnicalIndicators


class MomentumStrategy(BaseStrategy):
    """
    Momentum strategy.

    Follows the trend - buy when momentum is strong upward,
    sell when momentum weakens or reverses.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize momentum strategy.

        Config parameters:
            - momentum_period: Period for momentum calculation (default: 14)
            - rsi_period: RSI period (default: 14)
            - rsi_overbought: RSI overbought level (default: 70)
            - rsi_oversold: RSI oversold level (default: 30)
            - use_macd: Use MACD for confirmation (default: True)
            - trailing_stop_percent: Trailing stop percentage (default: 3)
        """
        super().__init__(config)

        self.momentum_period = config.get('momentum_period', 14)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.use_macd = config.get('use_macd', True)
        self.trailing_stop_percent = config.get('trailing_stop_percent', 3)

        self.highest_price = 0.0  # For trailing stop

    def calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate price momentum."""
        closes = data['close'].values
        if len(closes) < self.momentum_period:
            return 0

        current_price = closes[-1]
        past_price = closes[-self.momentum_period]

        momentum = ((current_price - past_price) / past_price) * 100
        return momentum

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """Generate momentum signal."""
        current_price = data['close'].iloc[-1]

        # Calculate indicators
        momentum = self.calculate_momentum(data)
        rsi = TechnicalIndicators.calculate_rsi(data['close'].values, self.rsi_period)[-1]

        # Update highest price for trailing stop
        if self.position > 0 and current_price > self.highest_price:
            self.highest_price = current_price

        # MACD confirmation (if enabled)
        macd_bullish = True
        if self.use_macd:
            macd, signal, _ = TechnicalIndicators.calculate_macd(data['close'].values)
            macd_bullish = macd[-1] > signal[-1]

        # BUY Signal: Strong positive momentum + RSI oversold/neutral + MACD bullish
        if (self.position == 0 and
            momentum > 2 and
            rsi < 60 and
            macd_bullish):

            return TradingSignal(
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=min((momentum / 10), 1.0),
                reason=f"Strong momentum ({momentum:.2f}%), RSI: {rsi:.2f}",
                metadata={'momentum': momentum, 'rsi': rsi}
            )

        # SELL Signal: Momentum weakening OR RSI overbought OR trailing stop hit
        if self.position > 0:
            # Trailing stop
            if self.highest_price > 0:
                drawdown_percent = ((self.highest_price - current_price) / self.highest_price) * 100
                if drawdown_percent > self.trailing_stop_percent:
                    return TradingSignal(
                        signal_type=SignalType.SELL,
                        price=current_price,
                        confidence=1.0,
                        reason=f"Trailing stop triggered (drawdown: {drawdown_percent:.2f}%)",
                        metadata={'trailing_stop': True}
                    )

            # Momentum reversal
            if momentum < -1:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.8,
                    reason=f"Momentum reversal ({momentum:.2f}%)",
                    metadata={'momentum': momentum}
                )

            # RSI overbought
            if rsi > self.rsi_overbought:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.7,
                    reason=f"RSI overbought ({rsi:.2f})",
                    metadata={'rsi': rsi}
                )

        return TradingSignal(
            signal_type=SignalType.HOLD,
            price=current_price,
            reason="No momentum signal"
        )

    def should_enter(self, data: pd.DataFrame) -> bool:
        """Check if should enter position."""
        if self.position > 0:
            return False

        momentum = self.calculate_momentum(data)
        rsi = TechnicalIndicators.calculate_rsi(data['close'].values, self.rsi_period)[-1]

        return momentum > 2 and rsi < 60

    def should_exit(self, data: pd.DataFrame) -> bool:
        """Check if should exit position."""
        if self.position == 0:
            return False

        current_price = data['close'].iloc[-1]
        momentum = self.calculate_momentum(data)

        # Trailing stop
        if self.highest_price > 0:
            drawdown_percent = ((self.highest_price - current_price) / self.highest_price) * 100
            if drawdown_percent > self.trailing_stop_percent:
                return True

        # Momentum reversal
        return momentum < -1

    def reset(self):
        """Reset strategy state."""
        super().reset()
        self.highest_price = 0.0


class BreakoutStrategy(BaseStrategy):
    """
    Breakout trading strategy.

    Identifies price breakouts from consolidation ranges and trades
    in the direction of the breakout.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize breakout strategy.

        Config parameters:
            - lookback_period: Period for identifying range (default: 20)
            - breakout_threshold: Percentage above/below range for breakout (default: 1)
            - volume_confirmation: Require volume spike for breakout (default: True)
            - volume_multiplier: Volume multiplier for confirmation (default: 1.5)
            - stop_loss_percent: Stop loss percentage (default: 3)
        """
        super().__init__(config)

        self.lookback_period = config.get('lookback_period', 20)
        self.breakout_threshold = config.get('breakout_threshold', 1)
        self.volume_confirmation = config.get('volume_confirmation', True)
        self.volume_multiplier = config.get('volume_multiplier', 1.5)
        self.stop_loss_percent = config.get('stop_loss_percent', 3)

        self.range_high = 0.0
        self.range_low = 0.0

    def identify_range(self, data: pd.DataFrame):
        """Identify price range."""
        recent_data = data.tail(self.lookback_period)
        self.range_high = recent_data['high'].max()
        self.range_low = recent_data['low'].min()

    def is_volume_spike(self, data: pd.DataFrame) -> bool:
        """Check for volume spike."""
        if not self.volume_confirmation:
            return True

        recent_volume = data['volume'].tail(self.lookback_period)
        avg_volume = recent_volume.mean()
        current_volume = data['volume'].iloc[-1]

        return current_volume > (avg_volume * self.volume_multiplier)

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """Generate breakout signal."""
        current_price = data['close'].iloc[-1]
        current_high = data['high'].iloc[-1]
        current_low = data['low'].iloc[-1]

        # Identify current range
        self.identify_range(data)

        # Calculate breakout levels
        breakout_high = self.range_high * (1 + self.breakout_threshold / 100)
        breakout_low = self.range_low * (1 - self.breakout_threshold / 100)

        # Upward breakout
        if (self.position == 0 and
            current_high > breakout_high and
            self.is_volume_spike(data)):

            return TradingSignal(
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=0.9,
                reason=f"Upward breakout above {self.range_high:.2f}",
                metadata={
                    'breakout_level': self.range_high,
                    'current_price': current_price,
                    'volume_spike': self.is_volume_spike(data)
                }
            )

        # Stop loss for long position
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

            # Exit if price falls back into range
            if current_price < self.range_high:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.7,
                    reason="Price fell back into range",
                    metadata={'failed_breakout': True}
                )

        return TradingSignal(
            signal_type=SignalType.HOLD,
            price=current_price,
            reason="No breakout detected"
        )

    def should_enter(self, data: pd.DataFrame) -> bool:
        """Check if should enter position."""
        if self.position > 0:
            return False

        current_high = data['high'].iloc[-1]
        self.identify_range(data)
        breakout_high = self.range_high * (1 + self.breakout_threshold / 100)

        return current_high > breakout_high and self.is_volume_spike(data)

    def should_exit(self, data: pd.DataFrame) -> bool:
        """Check if should exit position."""
        if self.position == 0:
            return False

        current_price = data['close'].iloc[-1]

        # Stop loss
        if self.entry_price > 0:
            loss_percent = ((current_price - self.entry_price) / self.entry_price) * 100
            if loss_percent < -self.stop_loss_percent:
                return True

        # Failed breakout
        if current_price < self.range_high:
            return True

        return False
