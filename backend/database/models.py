"""SQLAlchemy database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Enum, JSON, Text, Index, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class OrderSide(str, enum.Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class BotStatus(str, enum.Enum):
    """Trading bot status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("ExchangeAPIKey", back_populates="user", cascade="all, delete-orphan")
    bots = relationship("TradingBot", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class ExchangeAPIKey(Base):
    """Exchange API key storage (encrypted)."""
    __tablename__ = "exchange_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exchange = Column(String(50), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    encrypted_passphrase = Column(Text, nullable=True)  # For Coinbase, KuCoin
    is_testnet = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("idx_user_exchange", "user_id", "exchange"),
    )


class TradingBot(Base):
    """Trading bot configuration and state."""
    __tablename__ = "trading_bots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    strategy = Column(String(100), nullable=False)  # grid, mean_reversion, momentum, etc.
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    status = Column(Enum(BotStatus), default=BotStatus.STOPPED)

    # Configuration
    config = Column(JSON, nullable=False)  # Strategy-specific parameters

    # Performance tracking
    initial_capital = Column(Numeric(20, 8), nullable=False)
    current_capital = Column(Numeric(20, 8), nullable=False)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit_loss = Column(Numeric(20, 8), default=0)
    max_drawdown = Column(Float, default=0)

    # Risk management
    stop_loss_percent = Column(Float, nullable=True)
    take_profit_percent = Column(Float, nullable=True)
    max_position_size = Column(Numeric(20, 8), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="bots")
    orders = relationship("Order", back_populates="bot", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")


class Order(Base):
    """Order model."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=True)
    exchange_order_id = Column(String(200), nullable=True)

    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

    price = Column(Numeric(20, 8), nullable=True)  # Null for market orders
    amount = Column(Numeric(20, 8), nullable=False)
    filled_amount = Column(Numeric(20, 8), default=0)
    remaining_amount = Column(Numeric(20, 8), nullable=False)

    # For stop/take profit orders
    stop_price = Column(Numeric(20, 8), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    bot = relationship("TradingBot", back_populates="orders")

    __table_args__ = (
        Index("idx_orders_bot", "bot_id"),
        Index("idx_orders_symbol", "symbol", "created_at"),
        Index("idx_orders_status", "status"),
    )


class Trade(Base):
    """Trade execution record."""
    __tablename__ = "trades_executed"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)

    price = Column(Numeric(20, 8), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    commission = Column(Numeric(20, 8), default=0)
    commission_asset = Column(String(20), nullable=True)

    profit_loss = Column(Numeric(20, 8), nullable=True)
    profit_loss_percent = Column(Float, nullable=True)

    executed_at = Column(DateTime, default=datetime.utcnow)

    bot = relationship("TradingBot", back_populates="trades")

    __table_args__ = (
        Index("idx_trades_bot", "bot_id", "executed_at"),
        Index("idx_trades_symbol", "symbol", "executed_at"),
    )


class Alert(Base):
    """Alert configuration."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(200), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price, indicator, bot_status

    # Configuration
    config = Column(JSON, nullable=False)  # Alert-specific parameters

    # Notification channels
    notify_email = Column(Boolean, default=False)
    notify_sms = Column(Boolean, default=False)
    notify_telegram = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class AuditLog(Base):
    """Audit log for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(100), nullable=False)  # login, create_bot, execute_trade, etc.
    resource_type = Column(String(50), nullable=True)  # bot, order, api_key, etc.
    resource_id = Column(Integer, nullable=True)

    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user", "user_id", "created_at"),
        Index("idx_audit_action", "action", "created_at"),
    )


class BacktestResult(Base):
    """Backtest result storage."""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    strategy = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Configuration
    strategy_config = Column(JSON, nullable=False)

    # Performance metrics
    initial_capital = Column(Numeric(20, 8), nullable=False)
    final_capital = Column(Numeric(20, 8), nullable=False)
    total_return = Column(Float, nullable=False)
    total_return_percent = Column(Float, nullable=False)

    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0)

    max_drawdown = Column(Float, default=0)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)

    # Detailed results
    equity_curve = Column(JSON, nullable=True)  # Time series of portfolio value
    trades_log = Column(JSON, nullable=True)  # List of all trades

    created_at = Column(DateTime, default=datetime.utcnow)


class MLModel(Base):
    """ML model metadata and versioning."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False)  # lstm, prophet, random_forest
    version = Column(String(50), nullable=False)

    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)

    # Training info
    features = Column(JSON, nullable=False)
    hyperparameters = Column(JSON, nullable=False)

    # Performance metrics
    train_score = Column(Float, nullable=True)
    test_score = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)

    # Model storage
    model_path = Column(String(500), nullable=False)

    is_active = Column(Boolean, default=True)

    trained_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ml_model_symbol", "symbol", "model_type"),
    )
