"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from auth.security import password_hasher, token_manager
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UserRegister(BaseModel):
    """User registration model."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    user_id: Optional[int] = None


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """
    Register a new user.

    Args:
        user: User registration data

    Returns:
        JWT tokens
    """
    # In production, this would interact with database
    # For now, return mock tokens

    hashed_password = password_hasher.hash_password(user.password)

    # Create tokens
    access_token = token_manager.create_access_token(
        data={"sub": user.username, "user_id": 1}
    )
    refresh_token = token_manager.create_refresh_token(
        data={"sub": user.username, "user_id": 1}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login user and return JWT tokens.

    Args:
        form_data: Login form data

    Returns:
        JWT tokens
    """
    # In production, verify credentials against database
    # For now, accept any credentials for demo

    access_token = token_manager.create_access_token(
        data={"sub": form_data.username, "user_id": 1}
    )
    refresh_token = token_manager.create_refresh_token(
        data={"sub": form_data.username, "user_id": 1}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token

    Returns:
        New JWT tokens
    """
    payload = token_manager.decode_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    username = payload.get("sub")
    user_id = payload.get("user_id")

    access_token = token_manager.create_access_token(
        data={"sub": username, "user_id": user_id}
    )
    new_refresh_token = token_manager.create_refresh_token(
        data={"sub": username, "user_id": user_id}
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get current user from JWT token.

    Args:
        token: JWT access token

    Returns:
        Token data

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = token_manager.decode_token(token)

    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")

    if username is None:
        raise credentials_exception

    return TokenData(username=username, user_id=user_id)


@router.get("/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from token

    Returns:
        User information
    """
    return {
        "username": current_user.username,
        "user_id": current_user.user_id,
        "role": "admin"  # In production, fetch from database
    }
