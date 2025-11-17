"""Risk management system."""
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from dataclasses import dataclass
from loguru import logger
from scipy import stats


@dataclass
class RiskMetrics:
    """Risk assessment metrics."""
    var_95: float  # Value at Risk at 95% confidence
    var_99: float  # Value at Risk at 99% confidence
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    beta: float
    exposure: float


class PositionSizer:
    """Calculate optimal position sizes."""

    @staticmethod
    def fixed_fractional(
        capital: float,
        risk_per_trade_percent: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate position size using fixed fractional method.

        Args:
            capital: Available capital
            risk_per_trade_percent: % of capital to risk per trade
            entry_price: Entry price
            stop_loss_price: Stop loss price

        Returns:
            Position size
        """
        risk_amount = capital * (risk_per_trade_percent / 100)
        price_risk_per_unit = abs(entry_price - stop_loss_price)

        if price_risk_per_unit == 0:
            return 0

        position_size = risk_amount / price_risk_per_unit
        return position_size

    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion.

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size
            capital: Available capital

        Returns:
            Position size
        """
        if avg_loss == 0:
            return 0

        win_loss_ratio = avg_win / abs(avg_loss)

        # Kelly percentage
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Use fractional Kelly (half Kelly is common)
        kelly_pct = max(0, min(kelly_pct, 0.25))  # Cap at 25%

        position_value = capital * kelly_pct
        return position_value

    @staticmethod
    def volatility_based(
        capital: float,
        target_volatility: float,
        asset_volatility: float,
        price: float
    ) -> float:
        """
        Calculate position size based on volatility targeting.

        Args:
            capital: Available capital
            target_volatility: Target portfolio volatility
            asset_volatility: Asset volatility
            price: Current asset price

        Returns:
            Position size (number of units)
        """
        if asset_volatility == 0:
            return 0

        position_value = capital * (target_volatility / asset_volatility)
        position_size = position_value / price

        return position_size


class RiskManager:
    """Comprehensive risk management system."""

    def __init__(
        self,
        max_position_size: float = 10000,
        max_drawdown_percent: float = 20,
        var_confidence_level: float = 0.95,
        position_size_method: str = 'fixed_fractional',
        risk_per_trade_percent: float = 2.0
    ):
        """
        Initialize risk manager.

        Args:
            max_position_size: Maximum position size
            max_drawdown_percent: Maximum allowable drawdown %
            var_confidence_level: VaR confidence level
            position_size_method: Position sizing method
            risk_per_trade_percent: Risk per trade %
        """
        self.max_position_size = max_position_size
        self.max_drawdown_percent = max_drawdown_percent
        self.var_confidence_level = var_confidence_level
        self.position_size_method = position_size_method
        self.risk_per_trade_percent = risk_per_trade_percent

    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Return series
            confidence_level: Confidence level (0.95 = 95%)
            method: 'historical' or 'parametric'

        Returns:
            VaR value
        """
        if method == 'historical':
            # Historical VaR
            var = np.percentile(returns, (1 - confidence_level) * 100)
        else:  # parametric
            # Parametric VaR (assumes normal distribution)
            mean = np.mean(returns)
            std = np.std(returns)
            var = mean - std * stats.norm.ppf(confidence_level)

        return var

    def calculate_cvar(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        CVaR is the expected loss given that we're in the worst (1-confidence_level)% of outcomes.

        Args:
            returns: Return series
            confidence_level: Confidence level

        Returns:
            CVaR value
        """
        var = self.calculate_var(returns, confidence_level)
        cvar = returns[returns <= var].mean()
        return cvar

    def calculate_portfolio_risk_metrics(
        self,
        returns: pd.Series,
        market_returns: Optional[pd.Series] = None
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.

        Args:
            returns: Portfolio returns
            market_returns: Market returns (for beta calculation)

        Returns:
            RiskMetrics object
        """
        # VaR
        var_95 = self.calculate_var(returns.values, 0.95)
        var_99 = self.calculate_var(returns.values, 0.99)
        cvar_95 = self.calculate_cvar(returns.values, 0.95)

        # Volatility
        volatility = returns.std() * np.sqrt(252)  # Annualized

        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Sharpe ratio
        excess_returns = returns - 0  # Assuming 0 risk-free rate
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Beta (if market returns provided)
        beta = 1.0
        if market_returns is not None and len(market_returns) == len(returns):
            covariance = returns.cov(market_returns)
            market_variance = market_returns.var()
            beta = covariance / market_variance if market_variance > 0 else 1.0

        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            beta=beta,
            exposure=0.0  # To be calculated based on current positions
        )

    def calculate_position_size(
        self,
        capital: float,
        price: float,
        stop_loss_price: Optional[float] = None,
        **kwargs
    ) -> float:
        """
        Calculate optimal position size.

        Args:
            capital: Available capital
            price: Current price
            stop_loss_price: Stop loss price
            **kwargs: Additional parameters for specific methods

        Returns:
            Position size
        """
        if self.position_size_method == 'fixed_fractional':
            if stop_loss_price is None:
                # Default stop loss at 5%
                stop_loss_price = price * 0.95

            size = PositionSizer.fixed_fractional(
                capital,
                self.risk_per_trade_percent,
                price,
                stop_loss_price
            )

        elif self.position_size_method == 'kelly':
            win_rate = kwargs.get('win_rate', 0.5)
            avg_win = kwargs.get('avg_win', 1.0)
            avg_loss = kwargs.get('avg_loss', 1.0)

            position_value = PositionSizer.kelly_criterion(
                win_rate, avg_win, avg_loss, capital
            )
            size = position_value / price

        elif self.position_size_method == 'volatility':
            target_vol = kwargs.get('target_volatility', 0.15)
            asset_vol = kwargs.get('asset_volatility', 0.30)

            size = PositionSizer.volatility_based(
                capital, target_vol, asset_vol, price
            )

        else:
            # Fixed size
            size = self.max_position_size / price

        # Apply maximum position size limit
        max_units = self.max_position_size / price
        size = min(size, max_units)

        return size

    def check_risk_limits(
        self,
        current_drawdown_percent: float,
        position_value: float,
        total_exposure: float
    ) -> Dict[str, bool]:
        """
        Check if risk limits are exceeded.

        Args:
            current_drawdown_percent: Current drawdown %
            position_value: Value of new position
            total_exposure: Total portfolio exposure

        Returns:
            Dictionary of limit checks
        """
        checks = {
            'drawdown_ok': current_drawdown_percent > -self.max_drawdown_percent,
            'position_size_ok': position_value <= self.max_position_size,
            'exposure_ok': total_exposure <= 0.95  # Max 95% exposure
        }

        checks['all_ok'] = all(checks.values())

        return checks

    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        method: str = 'atr',
        multiplier: float = 2.0,
        fixed_percent: float = 3.0
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price
            atr: Average True Range
            method: 'atr' or 'fixed'
            multiplier: ATR multiplier
            fixed_percent: Fixed percentage for fixed method

        Returns:
            Stop loss price
        """
        if method == 'atr':
            stop_loss = entry_price - (atr * multiplier)
        else:  # fixed
            stop_loss = entry_price * (1 - fixed_percent / 100)

        return stop_loss

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit price based on risk-reward ratio.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_reward_ratio: Desired risk:reward ratio

        Returns:
            Take profit price
        """
        risk = entry_price - stop_loss_price
        reward = risk * risk_reward_ratio
        take_profit = entry_price + reward

        return take_profit

    def diversification_check(
        self,
        portfolio: Dict[str, float],
        new_asset: str,
        new_position_value: float
    ) -> bool:
        """
        Check if adding a new position maintains diversification.

        Args:
            portfolio: Current portfolio {asset: value}
            new_asset: New asset to add
            new_position_value: Value of new position

        Returns:
            True if diversification is maintained
        """
        # Calculate total portfolio value
        total_value = sum(portfolio.values()) + new_position_value

        # Check if any single asset would exceed 30% of portfolio
        for asset, value in portfolio.items():
            if value / total_value > 0.30:
                return False

        # Check if new position would exceed 30%
        if new_position_value / total_value > 0.30:
            return False

        return True
