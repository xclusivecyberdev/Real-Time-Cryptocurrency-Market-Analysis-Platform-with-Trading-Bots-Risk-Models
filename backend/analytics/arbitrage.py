"""Statistical arbitrage signal detection."""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from loguru import logger
from scipy import stats


class ArbitrageDetector:
    """Detect arbitrage opportunities across exchanges."""

    def __init__(self, threshold_percent: float = 0.5):
        """
        Initialize arbitrage detector.

        Args:
            threshold_percent: Minimum price difference % to consider as opportunity
        """
        self.threshold_percent = threshold_percent

    def detect_simple_arbitrage(
        self,
        prices: Dict[str, float],
        trading_fees: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Detect simple arbitrage opportunities (price differences across exchanges).

        Args:
            prices: Dictionary mapping exchange name to price
            trading_fees: Optional dictionary of trading fees per exchange (default: 0.1%)

        Returns:
            List of arbitrage opportunities
        """
        if trading_fees is None:
            trading_fees = {exchange: 0.001 for exchange in prices.keys()}

        opportunities = []

        # Compare all exchange pairs
        exchanges = list(prices.keys())
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i + 1:]:
                buy_price = prices[buy_exchange]
                sell_price = prices[sell_exchange]

                # Calculate profit considering fees
                buy_fee = buy_price * trading_fees.get(buy_exchange, 0.001)
                sell_fee = sell_price * trading_fees.get(sell_exchange, 0.001)

                profit = sell_price - buy_price - buy_fee - sell_fee
                profit_percent = (profit / buy_price) * 100

                if abs(profit_percent) >= self.threshold_percent:
                    opportunities.append({
                        'buy_exchange': buy_exchange if profit > 0 else sell_exchange,
                        'sell_exchange': sell_exchange if profit > 0 else buy_exchange,
                        'buy_price': buy_price if profit > 0 else sell_price,
                        'sell_price': sell_price if profit > 0 else buy_price,
                        'profit_percent': abs(profit_percent),
                        'estimated_profit': abs(profit),
                        'direction': 'long' if profit > 0 else 'short'
                    })

        return sorted(opportunities, key=lambda x: x['profit_percent'], reverse=True)

    def detect_triangular_arbitrage(
        self,
        prices: Dict[Tuple[str, str], float],
        base_currency: str = 'USDT'
    ) -> List[Dict]:
        """
        Detect triangular arbitrage opportunities.

        Example: USDT -> BTC -> ETH -> USDT

        Args:
            prices: Dictionary mapping (from_currency, to_currency) to price
            base_currency: Starting currency for the cycle

        Returns:
            List of triangular arbitrage opportunities
        """
        opportunities = []

        # This is a simplified version - in production, you'd want to
        # enumerate all possible triangular paths
        # For now, we'll demonstrate the concept

        logger.info("Triangular arbitrage detection - implementation simplified for demonstration")

        return opportunities


class PairsTrading:
    """Statistical arbitrage using pairs trading strategy."""

    def __init__(self, lookback_period: int = 60):
        """
        Initialize pairs trading analyzer.

        Args:
            lookback_period: Lookback period for cointegration analysis
        """
        self.lookback_period = lookback_period

    def calculate_spread(
        self,
        price1: np.ndarray,
        price2: np.ndarray,
        hedge_ratio: Optional[float] = None
    ) -> Tuple[np.ndarray, float]:
        """
        Calculate spread between two price series.

        Args:
            price1: First price series
            price2: Second price series
            hedge_ratio: Optional hedge ratio (calculated if not provided)

        Returns:
            Tuple of (spread, hedge_ratio)
        """
        if hedge_ratio is None:
            # Calculate optimal hedge ratio using linear regression
            hedge_ratio = np.polyfit(price2, price1, 1)[0]

        spread = price1 - hedge_ratio * price2
        return spread, hedge_ratio

    def test_cointegration(
        self,
        price1: np.ndarray,
        price2: np.ndarray
    ) -> Tuple[bool, float, float]:
        """
        Test if two price series are cointegrated.

        Args:
            price1: First price series
            price2: Second price series

        Returns:
            Tuple of (is_cointegrated, p_value, hedge_ratio)
        """
        from statsmodels.tsa.stattools import coint

        # Perform cointegration test
        score, p_value, _ = coint(price1, price2)

        # Calculate hedge ratio
        spread, hedge_ratio = self.calculate_spread(price1, price2)

        # Typically p_value < 0.05 indicates cointegration
        is_cointegrated = p_value < 0.05

        return is_cointegrated, p_value, hedge_ratio

    def generate_signals(
        self,
        spread: np.ndarray,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.0
    ) -> np.ndarray:
        """
        Generate trading signals based on spread z-score.

        Args:
            spread: Spread time series
            entry_threshold: Z-score threshold for entry (default: 2.0)
            exit_threshold: Z-score threshold for exit (default: 0.0)

        Returns:
            Array of signals (-1: short spread, 0: no position, 1: long spread)
        """
        # Calculate z-score of spread
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        z_score = (spread - spread_mean) / spread_std

        signals = np.zeros(len(z_score))

        # Long spread when z-score is very negative (spread is undervalued)
        signals[z_score < -entry_threshold] = 1

        # Short spread when z-score is very positive (spread is overvalued)
        signals[z_score > entry_threshold] = -1

        # Exit when spread reverts to mean
        signals[np.abs(z_score) < exit_threshold] = 0

        return signals

    def calculate_half_life(self, spread: np.ndarray) -> float:
        """
        Calculate mean reversion half-life of spread.

        Args:
            spread: Spread time series

        Returns:
            Half-life in periods
        """
        spread_lag = np.roll(spread, 1)[1:]
        spread_diff = np.diff(spread)

        # Run regression: spread_diff = lambda * spread_lag + noise
        slope = np.polyfit(spread_lag, spread_diff, 1)[0]

        # Half-life = -ln(2) / ln(1 + lambda)
        half_life = -np.log(2) / np.log(1 + slope)

        return half_life


class CorrelationAnalyzer:
    """Analyze correlations between assets."""

    @staticmethod
    def calculate_correlation_matrix(
        returns: pd.DataFrame,
        method: str = 'pearson'
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for multiple assets.

        Args:
            returns: DataFrame with returns for each asset (columns are assets)
            method: Correlation method ('pearson', 'spearman', 'kendall')

        Returns:
            Correlation matrix
        """
        return returns.corr(method=method)

    @staticmethod
    def calculate_rolling_correlation(
        returns1: np.ndarray,
        returns2: np.ndarray,
        window: int = 30
    ) -> np.ndarray:
        """
        Calculate rolling correlation between two return series.

        Args:
            returns1: First return series
            returns2: Second return series
            window: Rolling window size

        Returns:
            Array of rolling correlations
        """
        df = pd.DataFrame({
            'returns1': returns1,
            'returns2': returns2
        })

        rolling_corr = df['returns1'].rolling(window=window).corr(df['returns2']).values
        return rolling_corr

    @staticmethod
    def find_highly_correlated_pairs(
        returns: pd.DataFrame,
        threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """
        Find pairs of assets with high correlation.

        Args:
            returns: DataFrame with returns for each asset
            threshold: Minimum correlation threshold

        Returns:
            List of tuples (asset1, asset2, correlation)
        """
        corr_matrix = returns.corr()
        pairs = []

        # Iterate through upper triangle of correlation matrix
        for i, asset1 in enumerate(corr_matrix.columns):
            for j, asset2 in enumerate(corr_matrix.columns[i + 1:], start=i + 1):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) >= threshold:
                    pairs.append((asset1, asset2, corr))

        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)

    @staticmethod
    def calculate_beta(
        asset_returns: np.ndarray,
        market_returns: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculate beta and alpha for an asset relative to market.

        Args:
            asset_returns: Asset return series
            market_returns: Market return series

        Returns:
            Tuple of (beta, alpha)
        """
        # Calculate covariance and variance
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        beta = covariance / market_variance
        alpha = np.mean(asset_returns) - beta * np.mean(market_returns)

        return beta, alpha
