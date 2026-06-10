from app.db.database import async_session
from app.core.security import decrypt_api_key
from app.db.models import User
from sqlalchemy import select


class UserContext:
    def __init__(self, device_id: str, api_key: str, provider: str, model: str):
        self.device_id = device_id
        self.api_key = api_key
        self.provider = provider
        self.model = model


async def get_user_context(
    device_id: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> UserContext:
    if not device_id:
        raise ValueError("device_id is required")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.device_id == device_id))
        user = result.scalar_one_or_none()

    if user and user.api_key and user.api_key_iv and not api_key:
        decrypted_key = decrypt_api_key(user.api_key, user.api_key_iv)
    elif api_key:
        decrypted_key = api_key
    else:
        raise ValueError("No API key available")

    return UserContext(
        device_id=device_id,
        api_key=decrypted_key,
        provider=provider or (user.provider if user else "openai"),
        model=model or (user.model if user else "gpt-4o"),
    )
