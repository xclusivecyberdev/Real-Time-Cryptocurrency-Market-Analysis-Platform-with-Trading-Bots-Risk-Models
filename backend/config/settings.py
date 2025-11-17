"""Application configuration settings."""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "CryptoMarketAnalysisPlatform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    CORS_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str

    # Exchange API Keys
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = True

    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    BYBIT_TESTNET: bool = True

    COINBASE_API_KEY: str = ""
    COINBASE_API_SECRET: str = ""
    COINBASE_PASSPHRASE: str = ""

    KRAKEN_API_KEY: str = ""
    KRAKEN_API_SECRET: str = ""

    KUCOIN_API_KEY: str = ""
    KUCOIN_API_SECRET: str = ""
    KUCOIN_PASSPHRASE: str = ""

    # WebSocket
    WS_RECONNECT_DELAY: int = 5
    WS_MAX_RECONNECT_ATTEMPTS: int = 10
    WS_PING_INTERVAL: int = 30

    # Trading
    PAPER_TRADING: bool = True
    DEFAULT_LEVERAGE: int = 1
    MAX_POSITION_SIZE: float = 10000.0
    COMMISSION_RATE: float = 0.001

    # Risk Management
    MAX_DRAWDOWN_PERCENT: float = 20.0
    POSITION_SIZE_METHOD: str = "kelly"
    RISK_PER_TRADE_PERCENT: float = 2.0
    VAR_CONFIDENCE_LEVEL: float = 0.95

    # Backtesting
    BACKTEST_INITIAL_CAPITAL: float = 10000.0
    BACKTEST_COMMISSION: float = 0.001
    BACKTEST_SLIPPAGE: float = 0.0005

    # ML Models
    ML_MODEL_PATH: str = "./ml/models/saved"
    ML_RETRAIN_INTERVAL_HOURS: int = 24
    LSTM_EPOCHS: int = 100
    PROPHET_PERIODS: int = 30

    # Alerts
    ENABLE_ALERTS: bool = True
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cryptoplatform.com"

    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    SMS_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Data Retention
    KEEP_TICK_DATA_DAYS: int = 7
    KEEP_1M_CANDLES_DAYS: int = 30
    KEEP_5M_CANDLES_DAYS: int = 90
    KEEP_1H_CANDLES_DAYS: int = 365
    KEEP_1D_CANDLES_DAYS: int = 1825

    # Feature Flags
    ENABLE_ML_PREDICTIONS: bool = True
    ENABLE_LIVE_TRADING: bool = False
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_ARBITRAGE_DETECTION: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def supported_exchanges(self) -> List[str]:
        """List of supported exchanges."""
        return ["binance", "bybit", "coinbase", "kraken", "kucoin"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
