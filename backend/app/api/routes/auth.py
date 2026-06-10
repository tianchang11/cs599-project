import logging
from fastapi import APIRouter, Header

from app.db.database import async_session
from app.core.security import encrypt_api_key, decrypt_api_key
from app.core.auth import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import SettingsUpdate, AuthResponse, RefreshTokenRequest, TokenResponse
from app.db.models import User
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def get_settings(device_id: str) -> dict:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.device_id == device_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"provider": None, "model": None, "hasApiKey": False}
        return {
            "provider": user.provider,
            "model": user.model,
            "hasApiKey": bool(user.api_key),
        }


@router.post("")
async def save_settings(data: SettingsUpdate, device_id: str) -> dict:
    cipher_key, iv = encrypt_api_key(data.apiKey)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.device_id == device_id))
        existing = result.scalar_one_or_none()

        if existing:
            existing.api_key = cipher_key
            existing.api_key_iv = iv
            existing.provider = data.provider
            existing.model = data.model
            user = existing
        else:
            user = User(
                device_id=device_id,
                api_key=cipher_key,
                api_key_iv=iv,
                provider=data.provider,
                model=data.model,
            )
            session.add(user)

        await session.commit()
        await session.refresh(user)

    return {"status": "ok"}


@router.post("/auth/token", response_model=AuthResponse)
async def create_token(device_id: str) -> AuthResponse:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.device_id == device_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(device_id=device_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

    access_token = create_access_token(user.id, user.device_id)
    refresh_token = create_refresh_token(user.id, user.device_id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        device_id=user.device_id,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest) -> TokenResponse:
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    device_id = payload.get("device_id")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(user.id, user.device_id)
    return TokenResponse(access_token=access_token)
