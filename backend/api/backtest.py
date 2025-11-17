"""Backtesting API endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

from api.auth import get_current_user, TokenData

router = APIRouter()


class BacktestRequest(BaseModel):
    """Backtest request model."""
    strategy: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    config: Dict[str, Any]


class BacktestResponse(BaseModel):
    """Backtest response model."""
    id: int
    strategy: str
    symbol: str
    initial_capital: float
    final_capital: float
    total_return_percent: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown_percent: float


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Run a backtest."""
    # Mock response
    return BacktestResponse(
        id=1,
        strategy=request.strategy,
        symbol=request.symbol,
        initial_capital=request.initial_capital,
        final_capital=12500.0,
        total_return_percent=25.0,
        total_trades=50,
        win_rate=65.0,
        sharpe_ratio=1.8,
        max_drawdown_percent=-8.5
    )


@router.get("/results", response_model=List[BacktestResponse])
async def list_backtest_results(current_user: TokenData = Depends(get_current_user)):
    """List all backtest results."""
    return []


@router.get("/results/{backtest_id}")
async def get_backtest_result(
    backtest_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Get detailed backtest results."""
    return {
        "id": backtest_id,
        "metrics": {},
        "equity_curve": [],
        "trades": []
    }
