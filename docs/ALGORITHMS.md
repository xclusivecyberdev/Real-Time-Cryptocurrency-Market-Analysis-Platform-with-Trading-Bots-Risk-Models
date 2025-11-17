# Trading Algorithms & Models Documentation

## Technical Indicators

### RSI (Relative Strength Index)

**Purpose**: Identify overbought/oversold conditions

**Formula**:
```
RS = Average Gain / Average Loss
RSI = 100 - (100 / (1 + RS))
```

**Parameters**:
- Period: 14 (default)
- Overbought threshold: 70
- Oversold threshold: 30

**Trading Signals**:
- RSI < 30: Oversold → Buy signal
- RSI > 70: Overbought → Sell signal

**Implementation**: `backend/analytics/indicators.py:calculate_rsi()`

### MACD (Moving Average Convergence Divergence)

**Purpose**: Trend-following momentum indicator

**Formula**:
```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line
```

**Trading Signals**:
- Bullish crossover: MACD crosses above signal line → Buy
- Bearish crossover: MACD crosses below signal line → Sell

**Implementation**: `backend/analytics/indicators.py:calculate_macd()`

### Bollinger Bands

**Purpose**: Volatility-based support/resistance levels

**Formula**:
```
Middle Band = SMA(20)
Upper Band = Middle Band + (2 × Standard Deviation)
Lower Band = Middle Band - (2 × Standard Deviation)
```

**Trading Signals**:
- Price touches lower band → Potential buy
- Price touches upper band → Potential sell
- Band squeeze → Volatility breakout expected

**Implementation**: `backend/analytics/indicators.py:calculate_bollinger_bands()`

## Advanced Analytics

### GARCH (Generalized Autoregressive Conditional Heteroskedasticity)

**Purpose**: Forecast volatility

**Model**: GARCH(1,1)
```
σ²ₜ = ω + α × ε²ₜ₋₁ + β × σ²ₜ₋₁
```

Where:
- σ²ₜ: Conditional variance at time t
- ε²ₜ₋₁: Squared residual from previous period
- ω, α, β: Model parameters

**Use Cases**:
- Option pricing
- Risk management
- Volatility trading

**Implementation**: `backend/analytics/models/garch.py:GARCHModel`

### Statistical Arbitrage

**Purpose**: Exploit price inefficiencies across markets

**Methods**:

1. **Simple Arbitrage**
   - Detect price differences across exchanges
   - Account for trading fees and slippage
   - Execute when profit > threshold

2. **Pairs Trading**
   - Identify cointegrated pairs
   - Calculate spread and z-score
   - Trade mean reversion

**Cointegration Test**:
```python
# Augmented Dickey-Fuller test on spread
spread = price1 - hedge_ratio × price2
if p_value < 0.05:
    # Pair is cointegrated
```

**Implementation**: `backend/analytics/arbitrage.py`

## Machine Learning Models

### LSTM (Long Short-Term Memory)

**Purpose**: Time-series price prediction

**Architecture**:
```
Input Layer → LSTM(64) → LSTM(64) → Dense(32) → Dense(1)
```

**Features**:
- OHLCV data
- Technical indicators
- Lagged values
- Volume metrics

**Training**:
- Loss function: MSE (Mean Squared Error)
- Optimizer: Adam
- Sequence length: 60 periods
- Epochs: 100 (with early stopping)

**Performance Metrics**:
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² Score

**Implementation**: `ml/models/lstm/lstm_predictor.py`

### Prophet

**Purpose**: Time-series forecasting with seasonality

**Components**:
- Trend: Piecewise linear or logistic growth
- Seasonality: Daily, weekly patterns
- Holidays: Market events
- Additional regressors: Volume, sentiment

**Model**:
```
y(t) = g(t) + s(t) + h(t) + εₜ
```

Where:
- g(t): Trend
- s(t): Seasonality
- h(t): Holidays
- εₜ: Error term

**Hyperparameters**:
- changepoint_prior_scale: 0.05 (trend flexibility)
- seasonality_prior_scale: 10.0 (seasonality strength)
- seasonality_mode: 'multiplicative'

**Implementation**: `ml/models/prophet/prophet_predictor.py`

### Random Forest

**Purpose**: Classification (price direction) and regression (price prediction)

**Architecture**:
- n_estimators: 100
- max_depth: None (full depth)
- min_samples_split: 2
- Features: 20-50 engineered features

**Feature Engineering**:
1. **Price-based**: Returns, momentum, volatility
2. **Technical**: RSI, MACD, EMA ratios
3. **Lagged**: Previous periods (1, 2, 3, 5, 10)
4. **Volume**: Volume change, volume MA ratio

**Feature Importance**:
Top features typically:
- Recent price momentum
- RSI
- Volume metrics
- Lagged returns

**Implementation**: `ml/models/random_forest/rf_predictor.py`

## Trading Strategies

### Grid Trading

**Concept**: Place buy/sell orders at regular intervals

**Algorithm**:
```
1. Define grid:
   - Base price
   - Price range (±10%)
   - Number of levels (10)

2. Create orders:
   - Buy orders below base price
   - Sell orders above base price

3. Execute:
   - When price crosses grid level → Execute order
   - Profit from volatility
```

**Parameters**:
- Grid levels: 10
- Price range: 10%
- Investment per grid: $100
- Spacing: Arithmetic or geometric

**Pros**: Profits in ranging markets
**Cons**: Loses in strong trends

**Implementation**: `backend/trading/strategies/grid_trading.py`

### Mean Reversion

**Concept**: Price reverts to mean after deviation

**Algorithm**:
```
1. Calculate z-score:
   z = (price - mean) / std

2. Entry signals:
   - z < -2.0 → Buy (oversold)
   - z > 2.0 → Sell/Short (overbought)

3. Exit signals:
   - |z| < 0.5 → Close position
```

**Parameters**:
- Lookback period: 20
- Entry threshold: 2.0 std dev
- Exit threshold: 0.5 std dev
- Stop loss: 5%

**Variations**:
- Bollinger Bands version
- Pairs trading
- Statistical arbitrage

**Implementation**: `backend/trading/strategies/mean_reversion.py`

### Momentum

**Concept**: Trend continuation - ride the trend

**Algorithm**:
```
1. Identify momentum:
   - Calculate price change over period
   - RSI confirmation

2. Entry:
   - Momentum > 2% AND RSI < 60 → Buy

3. Exit:
   - Trailing stop: 3% from peak
   - Momentum reversal
   - RSI overbought
```

**Parameters**:
- Momentum period: 14
- RSI period: 14
- Trailing stop: 3%

**Pros**: Captures trends
**Cons**: Whipsaws in ranging markets

**Implementation**: `backend/trading/strategies/momentum.py`

### Breakout

**Concept**: Trade breakouts from consolidation ranges

**Algorithm**:
```
1. Identify range:
   - High: max(20 periods)
   - Low: min(20 periods)

2. Detect breakout:
   - Price > High × 1.01 → Upward breakout
   - Volume > avg_volume × 1.5 → Confirmed

3. Entry:
   - Buy on confirmed breakout

4. Exit:
   - Price falls back into range
   - Stop loss: 3%
```

**Parameters**:
- Lookback period: 20
- Breakout threshold: 1%
- Volume multiplier: 1.5
- Stop loss: 3%

**Implementation**: `backend/trading/strategies/momentum.py:BreakoutStrategy`

## Risk Management

### Position Sizing

**Methods**:

1. **Fixed Fractional**
   ```
   Position Size = (Capital × Risk%) / (Entry Price - Stop Loss Price)
   ```

2. **Kelly Criterion**
   ```
   Kelly% = (Win Rate × Avg Win - (1 - Win Rate)) / Avg Win
   Position Size = Capital × Kelly% × 0.5  # Half Kelly
   ```

3. **Volatility-Based**
   ```
   Position Size = (Capital × Target Vol) / (Asset Vol × Price)
   ```

**Implementation**: `backend/risk/manager.py:PositionSizer`

### Value at Risk (VaR)

**Purpose**: Estimate maximum potential loss

**Methods**:

1. **Historical VaR**
   ```
   VaR(95%) = 5th percentile of historical returns
   ```

2. **Parametric VaR**
   ```
   VaR = μ - σ × Z(confidence)
   ```

**Conditional VaR (CVaR)**:
```
CVaR = E[Loss | Loss > VaR]
```

**Implementation**: `backend/risk/manager.py:calculate_var()`

### Stop Loss & Take Profit

**Stop Loss Calculation**:

1. **ATR-based**
   ```
   Stop Loss = Entry Price - (ATR × Multiplier)
   ```

2. **Fixed Percentage**
   ```
   Stop Loss = Entry Price × (1 - Stop%)
   ```

**Take Profit**:
```
Risk = Entry Price - Stop Loss
Take Profit = Entry Price + (Risk × Risk:Reward Ratio)
```

**Implementation**: `backend/risk/manager.py`

## Performance Metrics

### Sharpe Ratio
```
Sharpe = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
```

### Sortino Ratio
```
Sortino = (Portfolio Return - Risk-Free Rate) / Downside Deviation
```

### Maximum Drawdown
```
DD = (Peak Value - Trough Value) / Peak Value
```

### Win Rate
```
Win Rate = Winning Trades / Total Trades × 100%
```

### Profit Factor
```
Profit Factor = Gross Profit / Gross Loss
```

## Model Accuracy & Validation

### Backtesting Methodology

1. **Walk-Forward Analysis**
   - Train on historical data
   - Test on out-of-sample data
   - Roll forward and repeat

2. **Cross-Validation**
   - Time-series split
   - Multiple folds
   - Aggregate metrics

3. **Transaction Costs**
   - Commission: 0.1%
   - Slippage: 0.05%
   - Include in backtest

### Overfitting Prevention

- Out-of-sample testing
- Regularization in ML models
- Simple strategies preferred
- Multiple market conditions tested

## References

1. Murphy, J. (1999). Technical Analysis of the Financial Markets
2. Chan, E. (2013). Algorithmic Trading
3. Lopez de Prado, M. (2018). Advances in Financial Machine Learning
4. Tsay, R. (2010). Analysis of Financial Time Series
