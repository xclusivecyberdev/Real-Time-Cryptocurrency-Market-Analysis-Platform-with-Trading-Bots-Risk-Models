"""Users API endpoints."""
from fastapi import APIRouter, Depends
from api.auth import get_current_user, TokenData

router = APIRouter()


@router.get("/profile")
async def get_user_profile(current_user: TokenData = Depends(get_current_user)):
    """Get user profile."""
    return {
        "username": current_user.username,
        "user_id": current_user.user_id,
        "email": "user@example.com",
        "role": "admin"
    }


@router.get("/stats")
async def get_user_stats(current_user: TokenData = Depends(get_current_user)):
    """Get user trading statistics."""
    return {
        "total_bots": 5,
        "active_bots": 3,
        "total_trades": 250,
        "total_pnl": 2500.50,
        "win_rate": 68.5
    }
