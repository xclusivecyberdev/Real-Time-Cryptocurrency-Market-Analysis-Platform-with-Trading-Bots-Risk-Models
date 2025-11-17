"""Base trading strategy interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradingSignal:
    """Trading signal data class."""
    signal_type: SignalType
    price: float
    amount: Optional[float] = None
    confidence: float = 1.0
    reason: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseStrategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy.

        Args:
            config: Strategy configuration parameters
        """
        self.config = config
        self.name = self.__class__.__name__
        self.position = 0.0  # Current position size
        self.entry_price = 0.0  # Average entry price
        self.signals_history: List[TradingSignal] = []

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """
        Generate trading signal based on market data.

        Args:
            data: Market data DataFrame with OHLCV and indicators

        Returns:
            TradingSignal object
        """
        pass

    @abstractmethod
    def should_enter(self, data: pd.DataFrame) -> bool:
        """
        Determine if should enter a position.

        Args:
            data: Market data

        Returns:
            True if should enter
        """
        pass

    @abstractmethod
    def should_exit(self, data: pd.DataFrame) -> bool:
        """
        Determine if should exit current position.

        Args:
            data: Market data

        Returns:
            True if should exit
        """
        pass

    def update_position(self, signal: TradingSignal, execution_price: float):
        """
        Update position after trade execution.

        Args:
            signal: Trading signal
            execution_price: Actual execution price
        """
        if signal.signal_type == SignalType.BUY:
            if self.position == 0:
                self.entry_price = execution_price
            else:
                # Update average entry price
                total_cost = self.position * self.entry_price + signal.amount * execution_price
                self.position += signal.amount
                self.entry_price = total_cost / self.position
            self.position += signal.amount or 0
        elif signal.signal_type == SignalType.SELL:
            self.position -= signal.amount or self.position
            if self.position == 0:
                self.entry_price = 0.0

        self.signals_history.append(signal)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get strategy performance metrics."""
        return {
            'total_signals': len(self.signals_history),
            'buy_signals': sum(1 for s in self.signals_history if s.signal_type == SignalType.BUY),
            'sell_signals': sum(1 for s in self.signals_history if s.signal_type == SignalType.SELL),
            'current_position': self.position,
            'entry_price': self.entry_price
        }

    def reset(self):
        """Reset strategy state."""
        self.position = 0.0
        self.entry_price = 0.0
        self.signals_history = []
