from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    model: type[T]

    async def get_session(self) -> AsyncSession:
        async with async_session() as session:
            return session

    async def get_by_id(self, id: str) -> Optional[T]:
        async with async_session() as session:
            result = await session.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()

    async def create(self, **kwargs) -> T:
        async with async_session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def update(self, id: str, **kwargs) -> Optional[T]:
        async with async_session() as session:
            result = await session.execute(select(self.model).where(self.model.id == id))
            instance = result.scalar_one_or_none()
            if not instance:
                return None
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def delete(self, id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(select(self.model).where(self.model.id == id))
            instance = result.scalar_one_or_none()
            if not instance:
                return False
            await session.delete(instance)
            await session.commit()
            return True
