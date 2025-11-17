# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=securepassword123
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response**:
```json
{
  "username": "johndoe",
  "user_id": 1,
  "role": "admin"
}
```

## Market Data Endpoints

#### Get Ticker
```http
GET /api/market/ticker/{exchange}/{symbol}
```

**Example**:
```http
GET /api/market/ticker/binance/BTC/USDT
```

**Response**:
```json
{
  "symbol": "BTC/USDT",
  "exchange": "binance",
  "last": 50000.0,
  "bid": 49995.0,
  "ask": 50005.0,
  "volume": 1234567.0,
  "change_24h": 2.5,
  "timestamp": "2023-12-01T10:30:00Z"
}
```

#### Get OHLCV Data
```http
GET /api/market/ohlcv/{exchange}/{symbol}?timeframe=1h&limit=100
```

**Query Parameters**:
- `timeframe`: 1m, 5m, 15m, 1h, 4h, 1d
- `limit`: Number of candles (1-1000)

**Response**:
```json
{
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": "2023-12-01T10:00:00Z",
      "open": 50000,
      "high": 50500,
      "low": 49500,
      "close": 50200,
      "volume": 123.45
    }
  ]
}
```

#### Get Supported Exchanges
```http
GET /api/market/exchanges
```

**Response**:
```json
{
  "exchanges": ["binance", "bybit", "coinbase", "kraken", "kucoin"]
}
```

## Trading Bots Endpoints

#### Create Trading Bot
```http
POST /api/bots
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Grid Bot BTC",
  "strategy": "grid_trading",
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "config": {
    "grid_levels": 10,
    "price_range_percent": 10,
    "investment_per_grid": 100
  },
  "initial_capital": 1000
}
```

**Response**:
```json
{
  "id": 1,
  "name": "Grid Bot BTC",
  "strategy": "grid_trading",
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "status": "stopped",
  "current_capital": 1000.0,
  "total_trades": 0,
  "win_rate": 0.0,
  "total_pnl": 0.0,
  "created_at": "2023-12-01T10:30:00Z"
}
```

#### List Trading Bots
```http
GET /api/bots
Authorization: Bearer <token>
```

**Response**:
```json
[
  {
    "id": 1,
    "name": "Grid Bot BTC",
    "strategy": "grid_trading",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "status": "running",
    "current_capital": 10500.0,
    "total_trades": 25,
    "win_rate": 72.0,
    "total_pnl": 500.0,
    "created_at": "2023-12-01T10:30:00Z"
  }
]
```

#### Start Bot
```http
POST /api/bots/{bot_id}/start
Authorization: Bearer <token>
```

**Response**:
```json
{
  "message": "Bot 1 started",
  "status": "running"
}
```

#### Stop Bot
```http
POST /api/bots/{bot_id}/stop
Authorization: Bearer <token>
```

#### Delete Bot
```http
DELETE /api/bots/{bot_id}
Authorization: Bearer <token>
```

## Analytics Endpoints

#### Get Technical Indicators
```http
GET /api/analytics/indicators/{symbol}?timeframe=1h
```

**Response**:
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "timestamp": "2023-12-01T10:30:00Z",
  "indicators": {
    "rsi": 55.2,
    "macd": {
      "macd": 150.5,
      "signal": 145.2,
      "histogram": 5.3
    },
    "bollinger_bands": {
      "upper": 51000,
      "middle": 50000,
      "lower": 49000
    },
    "ema_9": 49500,
    "ema_21": 49000,
    "ema_50": 48500
  }
}
```

#### Detect Arbitrage Opportunities
```http
GET /api/analytics/arbitrage?symbol=BTC/USDT
```

**Response**:
```json
{
  "symbol": "BTC/USDT",
  "opportunities": [
    {
      "buy_exchange": "binance",
      "sell_exchange": "coinbase",
      "buy_price": 50000,
      "sell_price": 50150,
      "profit_percent": 0.3,
      "estimated_profit": 150
    }
  ]
}
```

#### Get ML Predictions
```http
GET /api/analytics/predictions/{symbol}?model=lstm
```

**Query Parameters**:
- `model`: lstm, prophet, random_forest

**Response**:
```json
{
  "symbol": "BTC/USDT",
  "model": "lstm",
  "timestamp": "2023-12-01T10:30:00Z",
  "predictions": {
    "1h": 50200,
    "4h": 50500,
    "24h": 51000,
    "confidence": 0.75
  }
}
```

## Backtesting Endpoints

#### Run Backtest
```http
POST /api/backtest/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "strategy": "grid_trading",
  "symbol": "BTC/USDT",
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-12-31T23:59:59Z",
  "initial_capital": 10000,
  "config": {
    "grid_levels": 10,
    "price_range_percent": 10
  }
}
```

**Response**:
```json
{
  "id": 1,
  "strategy": "grid_trading",
  "symbol": "BTC/USDT",
  "initial_capital": 10000,
  "final_capital": 12500.0,
  "total_return_percent": 25.0,
  "total_trades": 50,
  "win_rate": 65.0,
  "sharpe_ratio": 1.8,
  "max_drawdown_percent": -8.5
}
```

#### Get Backtest Results
```http
GET /api/backtest/results/{backtest_id}
Authorization: Bearer <token>
```

## Alerts Endpoints

#### Create Alert
```http
POST /api/alerts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "BTC Price Alert",
  "alert_type": "price",
  "config": {
    "symbol": "BTC/USDT",
    "condition": "above",
    "price": 55000
  },
  "notify_email": true,
  "notify_telegram": true
}
```

**Response**:
```json
{
  "id": 1,
  "name": "BTC Price Alert",
  "alert_type": "price",
  "is_active": true,
  "last_triggered_at": null
}
```

#### List Alerts
```http
GET /api/alerts
Authorization: Bearer <token>
```

#### Delete Alert
```http
DELETE /api/alerts/{alert_id}
Authorization: Bearer <token>
```

## WebSocket Endpoints

### Market Data Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'ticker',
    symbol: 'BTC/USDT',
    exchange: 'binance'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Ticker update:', data);
};
```

### Bot Status Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/bots');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Bot update:', update);
};
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

- **Default**: 60 requests per minute per IP
- **Authenticated**: 100 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

## Pagination

List endpoints support pagination:

```http
GET /api/bots?page=1&limit=20
```

**Response**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.
