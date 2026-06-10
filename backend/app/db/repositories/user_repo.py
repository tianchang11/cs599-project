from typing import Optional

from sqlalchemy import select

from app.db.models import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_device_id(self, device_id: str) -> Optional[User]:
        from app.db.database import async_session
        async with async_session() as session:
            result = await session.execute(select(User).where(User.device_id == device_id))
            return result.scalar_one_or_none()

    async def get_or_create(self, device_id: str) -> User:
        user = await self.get_by_device_id(device_id)
        if user:
            return user
        return await self.create(device_id=device_id)
