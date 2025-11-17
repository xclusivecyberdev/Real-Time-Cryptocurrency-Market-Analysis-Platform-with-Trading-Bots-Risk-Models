"""Technical indicators implementation."""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import talib


class TechnicalIndicators:
    """Technical analysis indicators."""

    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: Array of closing prices
            period: RSI period (default: 14)

        Returns:
            Array of RSI values
        """
        return talib.RSI(prices, timeperiod=period)

    @staticmethod
    def calculate_macd(
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: Array of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Tuple of (macd, signal, histogram)
        """
        macd, signal, hist = talib.MACD(
            prices,
            fastperiod=fast_period,
            slowperiod=slow_period,
            signalperiod=signal_period
        )
        return macd, signal, hist

    @staticmethod
    def calculate_bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands.

        Args:
            prices: Array of closing prices
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        upper, middle, lower = talib.BBANDS(
            prices,
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev,
            matype=0
        )
        return upper, middle, lower

    @staticmethod
    def calculate_ema(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            prices: Array of closing prices
            period: EMA period

        Returns:
            Array of EMA values
        """
        return talib.EMA(prices, timeperiod=period)

    @staticmethod
    def calculate_sma(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            prices: Array of closing prices
            period: SMA period

        Returns:
            Array of SMA values
        """
        return talib.SMA(prices, timeperiod=period)

    @staticmethod
    def calculate_stochastic(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Stochastic Oscillator.

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices
            k_period: %K period
            d_period: %D period

        Returns:
            Tuple of (%K, %D)
        """
        slowk, slowd = talib.STOCH(
            high, low, close,
            fastk_period=k_period,
            slowk_period=d_period,
            slowk_matype=0,
            slowd_period=d_period,
            slowd_matype=0
        )
        return slowk, slowd

    @staticmethod
    def calculate_atr(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average True Range (ATR).

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices
            period: ATR period

        Returns:
            Array of ATR values
        """
        return talib.ATR(high, low, close, timeperiod=period)

    @staticmethod
    def calculate_adx(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average Directional Index (ADX).

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices
            period: ADX period

        Returns:
            Array of ADX values
        """
        return talib.ADX(high, low, close, timeperiod=period)

    @staticmethod
    def calculate_obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Calculate On-Balance Volume (OBV).

        Args:
            close: Array of closing prices
            volume: Array of volumes

        Returns:
            Array of OBV values
        """
        return talib.OBV(close, volume)

    @staticmethod
    def calculate_vwap(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Volume Weighted Average Price (VWAP).

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices
            volume: Array of volumes

        Returns:
            Array of VWAP values
        """
        typical_price = (high + low + close) / 3
        return np.cumsum(typical_price * volume) / np.cumsum(volume)

    @staticmethod
    def calculate_ichimoku(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> dict:
        """
        Calculate Ichimoku Cloud components.

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of closing prices

        Returns:
            Dictionary with Ichimoku components
        """
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        nine_period_high = pd.Series(high).rolling(window=9).max().values
        nine_period_low = pd.Series(low).rolling(window=9).min().values
        tenkan_sen = (nine_period_high + nine_period_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = pd.Series(high).rolling(window=26).max().values
        period26_low = pd.Series(low).rolling(window=26).min().values
        kijun_sen = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = pd.Series(high).rolling(window=52).max().values
        period52_low = pd.Series(low).rolling(window=52).min().values
        senkou_span_b = (period52_high + period52_low) / 2

        # Chikou Span (Lagging Span): Current closing price shifted back 26 periods
        chikou_span = close

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all common indicators for a DataFrame.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            DataFrame with added indicator columns
        """
        result = df.copy()

        # RSI
        result['rsi'] = TechnicalIndicators.calculate_rsi(df['close'].values)

        # MACD
        macd, signal, hist = TechnicalIndicators.calculate_macd(df['close'].values)
        result['macd'] = macd
        result['macd_signal'] = signal
        result['macd_hist'] = hist

        # Bollinger Bands
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df['close'].values)
        result['bb_upper'] = upper
        result['bb_middle'] = middle
        result['bb_lower'] = lower

        # EMAs
        result['ema_9'] = TechnicalIndicators.calculate_ema(df['close'].values, 9)
        result['ema_21'] = TechnicalIndicators.calculate_ema(df['close'].values, 21)
        result['ema_50'] = TechnicalIndicators.calculate_ema(df['close'].values, 50)
        result['ema_200'] = TechnicalIndicators.calculate_ema(df['close'].values, 200)

        # Stochastic
        slowk, slowd = TechnicalIndicators.calculate_stochastic(
            df['high'].values,
            df['low'].values,
            df['close'].values
        )
        result['stoch_k'] = slowk
        result['stoch_d'] = slowd

        # ATR
        result['atr'] = TechnicalIndicators.calculate_atr(
            df['high'].values,
            df['low'].values,
            df['close'].values
        )

        # ADX
        result['adx'] = TechnicalIndicators.calculate_adx(
            df['high'].values,
            df['low'].values,
            df['close'].values
        )

        # OBV
        result['obv'] = TechnicalIndicators.calculate_obv(
            df['close'].values,
            df['volume'].values
        )

        # VWAP
        result['vwap'] = TechnicalIndicators.calculate_vwap(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            df['volume'].values
        )

        return result


class SignalGenerator:
    """Generate trading signals from indicators."""

    @staticmethod
    def rsi_signals(rsi: np.ndarray, oversold: float = 30, overbought: float = 70) -> np.ndarray:
        """
        Generate buy/sell signals from RSI.

        Returns:
            1 for buy signal, -1 for sell signal, 0 for hold
        """
        signals = np.zeros(len(rsi))
        signals[rsi < oversold] = 1  # Buy signal
        signals[rsi > overbought] = -1  # Sell signal
        return signals

    @staticmethod
    def macd_signals(macd: np.ndarray, signal: np.ndarray) -> np.ndarray:
        """
        Generate buy/sell signals from MACD crossovers.

        Returns:
            1 for buy signal (bullish crossover), -1 for sell signal (bearish crossover), 0 for hold
        """
        signals = np.zeros(len(macd))
        diff = macd - signal

        # Bullish crossover: MACD crosses above signal
        signals[1:][np.diff(diff > 0) == True] = 1

        # Bearish crossover: MACD crosses below signal
        signals[1:][np.diff(diff > 0) == False] = -1

        return signals

    @staticmethod
    def bollinger_bands_signals(
        close: np.ndarray,
        upper: np.ndarray,
        lower: np.ndarray
    ) -> np.ndarray:
        """
        Generate buy/sell signals from Bollinger Bands.

        Returns:
            1 for buy signal, -1 for sell signal, 0 for hold
        """
        signals = np.zeros(len(close))
        signals[close < lower] = 1  # Buy when price touches lower band
        signals[close > upper] = -1  # Sell when price touches upper band
        return signals
