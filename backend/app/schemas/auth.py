from pydantic import BaseModel
from typing import Optional


class SettingsUpdate(BaseModel):
    apiKey: str
    provider: str
    model: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    device_id: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
