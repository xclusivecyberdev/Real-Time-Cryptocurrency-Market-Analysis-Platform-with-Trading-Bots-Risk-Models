# Quick Start Guide

Get your Crypto Market Analysis Platform up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- 4GB RAM minimum
- 10GB disk space

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd crypto-market-analysis-platform
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Generate secure keys:
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add these keys to your `.env` file.

### 3. Start the Platform
```bash
docker-compose up -d
```

Wait for all services to start (about 2 minutes):
```bash
docker-compose ps
```

### 4. Verify Installation
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0"
}
```

## Accessing the Platform

### Web Interfaces

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring (Grafana)**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`
- **Task Queue (Flower)**: http://localhost:5555

### First Steps

1. **Register an Account**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "trader1",
       "password": "secure_password_123"
     }'
   ```

2. **Login and Get Token**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=trader1&password=secure_password_123"
   ```

   Save the `access_token` from the response.

3. **View Market Data**
   ```bash
   curl http://localhost:8000/api/market/ticker/binance/BTC/USDT
   ```

## Create Your First Trading Bot

### Using the API

```bash
# Set your token
TOKEN="your_access_token_here"

# Create a grid trading bot
curl -X POST http://localhost:8000/api/bots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Grid Bot",
    "strategy": "grid_trading",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "config": {
      "grid_levels": 10,
      "price_range_percent": 5,
      "investment_per_grid": 100
    },
    "initial_capital": 1000
  }'
```

### Using Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/auth/login',
    data={
        'username': 'trader1',
        'password': 'secure_password_123'
    }
)
token = response.json()['access_token']

# Create bot
headers = {'Authorization': f'Bearer {token}'}
bot_config = {
    "name": "My First Grid Bot",
    "strategy": "grid_trading",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "config": {
        "grid_levels": 10,
        "price_range_percent": 5,
        "investment_per_grid": 100
    },
    "initial_capital": 1000
}

response = requests.post(
    'http://localhost:8000/api/bots',
    headers=headers,
    json=bot_config
)

bot = response.json()
print(f"Bot created! ID: {bot['id']}")

# Start the bot
bot_id = bot['id']
requests.post(
    f'http://localhost:8000/api/bots/{bot_id}/start',
    headers=headers
)
print("Bot started!")
```

## Run a Backtest

```python
import requests

headers = {'Authorization': f'Bearer {token}'}

backtest_config = {
    "strategy": "mean_reversion",
    "symbol": "BTC/USDT",
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-12-31T23:59:59Z",
    "initial_capital": 10000,
    "config": {
        "lookback_period": 20,
        "entry_threshold": 2.0,
        "exit_threshold": 0.5
    }
}

response = requests.post(
    'http://localhost:8000/api/backtest/run',
    headers=headers,
    json=backtest_config
)

results = response.json()
print(f"""
Backtest Results:
- Total Return: {results['total_return_percent']:.2f}%
- Total Trades: {results['total_trades']}
- Win Rate: {results['win_rate']:.2f}%
- Sharpe Ratio: {results['sharpe_ratio']:.2f}
- Max Drawdown: {results['max_drawdown_percent']:.2f}%
""")
```

## Set Up Alerts

```python
alert_config = {
    "name": "BTC Price Alert",
    "alert_type": "price",
    "config": {
        "symbol": "BTC/USDT",
        "condition": "above",
        "price": 60000
    },
    "notify_email": True,
    "notify_telegram": False
}

response = requests.post(
    'http://localhost:8000/api/alerts',
    headers=headers,
    json=alert_config
)

print("Alert created!")
```

## Common Operations

### List All Bots
```bash
curl http://localhost:8000/api/bots \
  -H "Authorization: Bearer $TOKEN"
```

### Get Market Indicators
```bash
curl "http://localhost:8000/api/analytics/indicators/BTC/USDT?timeframe=1h"
```

### Get ML Predictions
```bash
curl "http://localhost:8000/api/analytics/predictions/BTC/USDT?model=lstm"
```

### Detect Arbitrage Opportunities
```bash
curl "http://localhost:8000/api/analytics/arbitrage?symbol=BTC/USDT"
```

## Using the Frontend

1. Open http://localhost:3000 in your browser
2. Register/Login with your credentials
3. Navigate through:
   - **Dashboard**: View market overview
   - **Bots**: Create and manage trading bots
   - **Backtest**: Test strategies on historical data
   - **Analytics**: View indicators and predictions
   - **Alerts**: Set up price and indicator alerts

## Connect to Real Exchanges (Optional)

### For Paper Trading (Default)
Paper trading is enabled by default. No API keys needed.

### For Live Trading
1. Get API keys from your exchange:
   - Binance: https://www.binance.com/en/my/settings/api-management
   - Coinbase: https://www.coinbase.com/settings/api
   - Others: Check exchange documentation

2. Add to `.env`:
   ```env
   # Enable live trading
   PAPER_TRADING=false

   # Binance
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   BINANCE_TESTNET=false
   ```

3. Restart services:
   ```bash
   docker-compose restart
   ```

## Monitoring

### View Logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### Check Resource Usage
```bash
docker stats
```

### Access Grafana Dashboards
1. Go to http://localhost:3001
2. Login (admin/admin)
3. Navigate to Dashboards
4. View:
   - System Metrics
   - Trading Bot Performance
   - API Request Metrics

## Troubleshooting

### Services Won't Start
```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs

# Restart all services
docker-compose restart
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Connect to database manually
docker exec -it crypto_postgres psql -U crypto_user -d crypto_platform
```

### Can't Access Frontend
```bash
# Check if port 3000 is already in use
lsof -i :3000

# Restart frontend
docker-compose restart frontend
```

## Next Steps

- [Read the Full Documentation](docs/)
- [Learn About Trading Strategies](docs/ALGORITHMS.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Support

- GitHub Issues: <repository-url>/issues
- Documentation: [docs/](docs/)

## Important Disclaimers

⚠️ **Trading Risks**:
- Cryptocurrency trading carries significant risk
- You can lose all your invested capital
- Always start with paper trading
- Never invest more than you can afford to lose

⚠️ **Security**:
- Change default passwords in production
- Use strong, unique passwords
- Keep API keys secure
- Enable 2FA on exchange accounts

⚠️ **Legal**:
- Check your local regulations regarding cryptocurrency trading
- This platform is for educational purposes
- Use at your own risk

---

Happy Trading! 🚀📈
