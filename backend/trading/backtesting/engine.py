"""Backtesting engine for trading strategies."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from backend.trading.strategies.base import BaseStrategy, SignalType


@dataclass
class Trade:
    """Trade execution record."""
    timestamp: datetime
    signal_type: str
    price: float
    amount: float
    commission: float
    balance: float
    equity: float
    pnl: float = 0.0


@dataclass
class BacktestResult:
    """Backtest results."""
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    max_drawdown: float
    max_drawdown_percent: float

    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float

    avg_win: float
    avg_loss: float
    avg_win_loss_ratio: float

    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = None
    metrics_by_period: Dict[str, Any] = field(default_factory=dict)


class Backtester:
    """Backtesting engine for trading strategies."""

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        Initialize backtester.

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Starting capital
            commission: Trading commission rate (0.001 = 0.1%)
            slippage: Slippage rate
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        self.cash = initial_capital
        self.position = 0.0
        self.position_value = 0.0

        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []

    def calculate_commission(self, price: float, amount: float) -> float:
        """Calculate trading commission."""
        return price * amount * self.commission

    def apply_slippage(self, price: float, signal_type: SignalType) -> float:
        """Apply slippage to execution price."""
        if signal_type == SignalType.BUY:
            return price * (1 + self.slippage)
        elif signal_type == SignalType.SELL:
            return price * (1 - self.slippage)
        return price

    def execute_trade(
        self,
        timestamp: datetime,
        signal_type: SignalType,
        price: float,
        amount: Optional[float] = None
    ):
        """
        Execute a trade.

        Args:
            timestamp: Trade timestamp
            signal_type: Buy or sell
            price: Execution price
            amount: Trade amount (None = use all available)
        """
        # Apply slippage
        execution_price = self.apply_slippage(price, signal_type)

        if signal_type == SignalType.BUY:
            # Calculate maximum amount we can buy
            if amount is None:
                max_amount = self.cash / (execution_price * (1 + self.commission))
                amount = max_amount * 0.99  # Use 99% to be safe

            cost = execution_price * amount
            commission = self.calculate_commission(execution_price, amount)
            total_cost = cost + commission

            if total_cost <= self.cash:
                self.cash -= total_cost
                self.position += amount
                self.position_value = self.position * execution_price

                pnl = 0.0
            else:
                logger.warning(f"Insufficient cash for trade: {total_cost} > {self.cash}")
                return

        elif signal_type == SignalType.SELL:
            # Sell position
            if amount is None or amount > self.position:
                amount = self.position

            if amount == 0:
                return

            proceeds = execution_price * amount
            commission = self.calculate_commission(execution_price, amount)
            net_proceeds = proceeds - commission

            # Calculate PnL
            avg_cost = (self.initial_capital - self.cash + self.position_value) / self.position if self.position > 0 else 0
            pnl = (execution_price - avg_cost) * amount - commission

            self.cash += net_proceeds
            self.position -= amount
            self.position_value = self.position * execution_price if self.position > 0 else 0.0

        else:  # HOLD
            return

        # Record trade
        equity = self.cash + self.position_value
        trade = Trade(
            timestamp=timestamp,
            signal_type=signal_type.value,
            price=execution_price,
            amount=amount,
            commission=commission,
            balance=self.cash,
            equity=equity,
            pnl=pnl
        )
        self.trades.append(trade)
        self.equity_curve.append(equity)

    def run(
        self,
        data: pd.DataFrame,
        progress_callback: Optional[callable] = None
    ) -> BacktestResult:
        """
        Run backtest on historical data.

        Args:
            data: Historical OHLCV data
            progress_callback: Optional callback for progress updates

        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest with {len(data)} data points")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Initial capital: ${self.initial_capital:,.2f}")

        # Reset state
        self.cash = self.initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.strategy.reset()

        # Run through historical data
        for i in range(len(data)):
            if i < 50:  # Need some history for indicators
                continue

            # Get data up to current point
            current_data = data.iloc[:i+1]

            # Generate signal
            signal = self.strategy.generate_signal(current_data)

            # Execute trade
            if signal.signal_type != SignalType.HOLD:
                timestamp = current_data.index[-1] if isinstance(current_data.index, pd.DatetimeIndex) else datetime.now()
                self.execute_trade(
                    timestamp=timestamp,
                    signal_type=signal.signal_type,
                    price=signal.price,
                    amount=signal.amount
                )

                # Update strategy position
                self.strategy.update_position(signal, signal.price)

            # Update equity curve even if no trade
            else:
                current_price = current_data['close'].iloc[-1]
                self.position_value = self.position * current_price
                equity = self.cash + self.position_value
                self.equity_curve.append(equity)

            # Progress callback
            if progress_callback and i % 100 == 0:
                progress_callback(i, len(data))

        # Final liquidation
        if self.position > 0:
            final_price = data['close'].iloc[-1]
            final_timestamp = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else datetime.now()
            self.execute_trade(
                timestamp=final_timestamp,
                signal_type=SignalType.SELL,
                price=final_price,
                amount=self.position
            )

        # Calculate metrics
        result = self._calculate_metrics()

        logger.info(f"Backtest completed")
        logger.info(f"Final capital: ${result.final_capital:,.2f}")
        logger.info(f"Total return: {result.total_return_percent:.2f}%")
        logger.info(f"Total trades: {result.total_trades}")
        logger.info(f"Win rate: {result.win_rate:.2f}%")
        logger.info(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Max drawdown: {result.max_drawdown_percent:.2f}%")

        return result

    def _calculate_metrics(self) -> BacktestResult:
        """Calculate backtest performance metrics."""
        final_capital = self.cash
        total_return = final_capital - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100

        # Trade statistics
        buy_trades = [t for t in self.trades if t.signal_type == 'buy']
        sell_trades = [t for t in self.trades if t.signal_type == 'sell']

        winning_trades = [t for t in sell_trades if t.pnl > 0]
        losing_trades = [t for t in sell_trades if t.pnl < 0]

        total_trades = len(sell_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        # Average win/loss
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        avg_win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Profit factor
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Drawdown
        equity_series = pd.Series(self.equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = equity_series - running_max
        max_drawdown = drawdown.min()
        max_drawdown_percent = (max_drawdown / running_max[drawdown.idxmin()]) * 100 if len(running_max) > 0 else 0

        # Sharpe ratio
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 and returns.std() > 0 else 0

        # Sortino ratio (uses only downside deviation)
        downside_returns = returns[returns < 0]
        sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_win_loss_ratio=avg_win_loss_ratio,
            trades=self.trades,
            equity_curve=equity_series
        )
