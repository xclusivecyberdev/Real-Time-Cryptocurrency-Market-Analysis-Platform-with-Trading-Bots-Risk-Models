"""GARCH volatility modeling."""
import numpy as np
import pandas as pd
from arch import arch_model
from typing import Tuple, Optional
from loguru import logger


class GARCHModel:
    """GARCH volatility forecasting model."""

    def __init__(self, p: int = 1, q: int = 1):
        """
        Initialize GARCH model.

        Args:
            p: GARCH lag order
            q: ARCH lag order
        """
        self.p = p
        self.q = q
        self.model = None
        self.fitted_model = None

    def fit(self, returns: np.ndarray, vol: str = 'GARCH') -> 'GARCHModel':
        """
        Fit GARCH model to returns data.

        Args:
            returns: Array of returns (not prices)
            vol: Volatility process ('GARCH', 'EGARCH', 'GJR-GARCH')

        Returns:
            Self
        """
        try:
            # Convert to percentage returns
            returns_pct = returns * 100

            # Create and fit GARCH model
            self.model = arch_model(
                returns_pct,
                vol=vol,
                p=self.p,
                q=self.q,
                rescale=False
            )
            self.fitted_model = self.model.fit(disp='off')

            logger.info(f"GARCH({self.p},{self.q}) model fitted successfully")
            return self

        except Exception as e:
            logger.error(f"Failed to fit GARCH model: {e}")
            raise

    def forecast(self, horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forecast volatility.

        Args:
            horizon: Forecast horizon (number of periods ahead)

        Returns:
            Tuple of (mean_forecast, variance_forecast)
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        try:
            forecast = self.fitted_model.forecast(horizon=horizon)
            mean_forecast = forecast.mean.values[-1]
            variance_forecast = forecast.variance.values[-1]

            return mean_forecast, variance_forecast

        except Exception as e:
            logger.error(f"Failed to forecast with GARCH model: {e}")
            raise

    def get_conditional_volatility(self) -> np.ndarray:
        """
        Get conditional volatility from fitted model.

        Returns:
            Array of conditional volatility estimates
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return self.fitted_model.conditional_volatility

    def get_standardized_residuals(self) -> np.ndarray:
        """
        Get standardized residuals from fitted model.

        Returns:
            Array of standardized residuals
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return self.fitted_model.std_resid

    def summary(self) -> str:
        """Get model summary."""
        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return str(self.fitted_model.summary())


class VolatilityAnalyzer:
    """Analyze and forecast volatility patterns."""

    @staticmethod
    def calculate_realized_volatility(
        returns: np.ndarray,
        window: int = 20,
        annualize: bool = True
    ) -> np.ndarray:
        """
        Calculate realized volatility (rolling standard deviation).

        Args:
            returns: Array of returns
            window: Rolling window size
            annualize: Whether to annualize (multiply by sqrt(252) for daily data)

        Returns:
            Array of realized volatility
        """
        df = pd.DataFrame({'returns': returns})
        rolling_std = df['returns'].rolling(window=window).std().values

        if annualize:
            rolling_std *= np.sqrt(252)

        return rolling_std

    @staticmethod
    def calculate_parkinson_volatility(
        high: np.ndarray,
        low: np.ndarray,
        window: int = 20
    ) -> np.ndarray:
        """
        Calculate Parkinson volatility estimator (uses high-low range).

        More efficient than close-to-close volatility.

        Args:
            high: Array of high prices
            low: Array of low prices
            window: Rolling window size

        Returns:
            Array of Parkinson volatility estimates
        """
        hl_ratio = np.log(high / low)
        df = pd.DataFrame({'hl_ratio': hl_ratio})

        parkinson_vol = df['hl_ratio'].rolling(window=window).apply(
            lambda x: np.sqrt(np.sum(x ** 2) / (4 * len(x) * np.log(2)))
        ).values

        return parkinson_vol * np.sqrt(252)  # Annualize

    @staticmethod
    def calculate_garman_klass_volatility(
        open_: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        window: int = 20
    ) -> np.ndarray:
        """
        Calculate Garman-Klass volatility estimator.

        More efficient than Parkinson, uses OHLC data.

        Args:
            open_: Array of opening prices
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices
            window: Rolling window size

        Returns:
            Array of Garman-Klass volatility estimates
        """
        log_hl = np.log(high / low)
        log_co = np.log(close / open_)

        df = pd.DataFrame({
            'log_hl': log_hl,
            'log_co': log_co
        })

        def gk_vol(df_window):
            hl = df_window['log_hl'].values
            co = df_window['log_co'].values
            n = len(hl)
            return np.sqrt((1 / n) * (0.5 * np.sum(hl ** 2) - (2 * np.log(2) - 1) * np.sum(co ** 2)))

        rolling_gk = df.rolling(window=window).apply(gk_vol, raw=False)

        return rolling_gk['log_hl'].values * np.sqrt(252)  # Annualize

    @staticmethod
    def volatility_regime_detection(
        volatility: np.ndarray,
        low_threshold: float = 0.15,
        high_threshold: float = 0.30
    ) -> np.ndarray:
        """
        Detect volatility regimes (low, medium, high).

        Args:
            volatility: Array of volatility estimates
            low_threshold: Threshold for low volatility regime
            high_threshold: Threshold for high volatility regime

        Returns:
            Array of regime labels (0=low, 1=medium, 2=high)
        """
        regimes = np.zeros(len(volatility))
        regimes[volatility < low_threshold] = 0  # Low volatility
        regimes[(volatility >= low_threshold) & (volatility < high_threshold)] = 1  # Medium
        regimes[volatility >= high_threshold] = 2  # High volatility

        return regimes
