from typing import Optional

from sqlalchemy import select, desc

from app.db.models import Note
from app.db.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    model = Note

    async def list_by_user_id(self, user_id: str) -> list[Note]:
        from app.db.database import async_session
        async with async_session() as session:
            result = await session.execute(
                select(Note)
                .where(Note.user_id == user_id)
                .order_by(desc(Note.created_at))
            )
            return list(result.scalars().all())

    async def get_by_ids(self, note_ids: list[str]) -> list[Note]:
        if not note_ids:
            return []
        from app.db.database import async_session
        async with async_session() as session:
            result = await session.execute(
                select(Note).where(Note.id.in_(note_ids))
            )
            return list(result.scalars().all())
