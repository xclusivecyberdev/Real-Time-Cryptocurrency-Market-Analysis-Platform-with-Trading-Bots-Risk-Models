-- Initialize database with TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create timeseries tables
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open NUMERIC(20, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    close NUMERIC(20, 8),
    volume NUMERIC(20, 8),
    PRIMARY KEY (time, exchange, symbol)
);

-- Convert to hypertable
SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_exchange ON market_data (exchange, time DESC);

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    trade_id VARCHAR(100),
    side VARCHAR(10),
    price NUMERIC(20, 8),
    amount NUMERIC(20, 8),
    PRIMARY KEY (time, exchange, symbol, trade_id)
);

SELECT create_hypertable('trades', 'time', if_not_exists => TRUE);

-- Create order book snapshots table
CREATE TABLE IF NOT EXISTS order_book_snapshots (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    bids JSONB,
    asks JSONB,
    PRIMARY KEY (time, exchange, symbol)
);

SELECT create_hypertable('order_book_snapshots', 'time', if_not_exists => TRUE);

-- Create funding rates table
CREATE TABLE IF NOT EXISTS funding_rates (
    time TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    rate NUMERIC(20, 8),
    PRIMARY KEY (time, exchange, symbol)
);

SELECT create_hypertable('funding_rates', 'time', if_not_exists => TRUE);

-- Create compression policies
SELECT add_compression_policy('market_data', INTERVAL '7 days');
SELECT add_compression_policy('trades', INTERVAL '3 days');
SELECT add_compression_policy('order_book_snapshots', INTERVAL '1 day');
SELECT add_compression_policy('funding_rates', INTERVAL '30 days');

-- Create retention policies
SELECT add_retention_policy('market_data', INTERVAL '2 years');
SELECT add_retention_policy('trades', INTERVAL '90 days');
SELECT add_retention_policy('order_book_snapshots', INTERVAL '30 days');
SELECT add_retention_policy('funding_rates', INTERVAL '1 year');

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    exchange,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_data
GROUP BY bucket, exchange, symbol;

CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    exchange,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_data
GROUP BY bucket, exchange, symbol;

-- Add refresh policies
SELECT add_continuous_aggregate_policy('market_data_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('market_data_1d',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');
