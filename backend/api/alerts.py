"""Alerts API endpoints."""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from api.auth import get_current_user, TokenData

router = APIRouter()


class AlertCreate(BaseModel):
    """Alert creation model."""
    name: str
    alert_type: str  # price, indicator, bot_status
    config: Dict[str, Any]
    notify_email: bool = False
    notify_sms: bool = False
    notify_telegram: bool = False


class AlertResponse(BaseModel):
    """Alert response model."""
    id: int
    name: str
    alert_type: str
    is_active: bool
    last_triggered_at: datetime = None


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert: AlertCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new alert."""
    return AlertResponse(
        id=1,
        name=alert.name,
        alert_type=alert.alert_type,
        is_active=True
    )


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(current_user: TokenData = Depends(get_current_user)):
    """List all alerts."""
    return []


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: int, current_user: TokenData = Depends(get_current_user)):
    """Delete an alert."""
    return None
