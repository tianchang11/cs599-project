import json
from fastapi import APIRouter, HTTPException, Query

from app.db.database import async_session
from app.services.vector_service import vector_service
from app.schemas.library import NoteCreate, NoteUpdate, NoteResponse
from app.db.models import User, Note
from sqlalchemy import select, desc

router = APIRouter()


@router.get("")
async def list_notes(device_id: str = Query(...)) -> list[NoteResponse]:
    async with async_session() as session:
        result = await session.execute(
            select(Note, User)
            .join(User, Note.user_id == User.id)
            .where(User.device_id == device_id)
            .order_by(desc(Note.created_at))
        )
        rows = result.all()

        notes = []
        for note, user in rows:
            sources = json.loads(note.sources) if note.sources else []
            notes.append(NoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                sources=sources,
                query=note.query,
                createdAt=note.created_at.isoformat(),
                updatedAt=note.updated_at.isoformat(),
            ))
        return notes


@router.get("/search")
async def search_notes(
    q: str = Query(...),
    device_id: str = Query(...),
) -> list[NoteResponse]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.device_id == device_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []

        hits = vector_service.search_notes(q, user.id, top_k=10)
        note_ids = [h["id"] for h in hits]

        if not note_ids:
            return []

        result2 = await session.execute(
            select(Note)
            .where(Note.id.in_(note_ids))
            .order_by(desc(Note.created_at))
        )
        notes = result2.scalars().all()

        out = []
        for note in notes:
            sources = json.loads(note.sources) if note.sources else []
            out.append(NoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                sources=sources,
                query=note.query,
                createdAt=note.created_at.isoformat(),
                updatedAt=note.updated_at.isoformat(),
            ))
        return out


@router.get("/{note_id}")
async def get_note(note_id: str) -> NoteResponse:
    async with async_session() as session:
        result = await session.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    sources = json.loads(note.sources) if note.sources else []
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        sources=sources,
        query=note.query,
        createdAt=note.created_at.isoformat(),
        updatedAt=note.updated_at.isoformat(),
    )


@router.post("")
async def create_note(data: NoteCreate, device_id: str = Query(...)) -> NoteResponse:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.device_id == device_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(device_id=device_id)
            session.add(user)
            await session.flush()

        note = Note(
            user_id=user.id,
            title=data.title,
            content=data.content,
            sources=json.dumps(data.sources),
            query=data.query,
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

        try:
            vector_service.add_note(
                note_id=note.id,
                text=data.content,
                user_id=user.id,
                title=data.title,
                metadata={"query": data.query},
            )
        except Exception:
            pass

        sources = json.loads(note.sources) if note.sources else []
        return NoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            sources=sources,
            query=note.query,
            createdAt=note.created_at.isoformat(),
            updatedAt=note.updated_at.isoformat(),
        )


@router.put("/{note_id}")
async def update_note(note_id: str, data: NoteUpdate) -> NoteResponse:
    async with async_session() as session:
        result = await session.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        if data.title is not None:
            note.title = data.title
        if data.content is not None:
            note.content = data.content

        await session.commit()
        await session.refresh(note)

        sources = json.loads(note.sources) if note.sources else []
        return NoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            sources=sources,
            query=note.query,
            createdAt=note.created_at.isoformat(),
            updatedAt=note.updated_at.isoformat(),
        )


@router.delete("/{note_id}")
async def delete_note(note_id: str):
    async with async_session() as session:
        result = await session.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        await session.delete(note)
        await session.commit()

    try:
        vector_service.delete_note(note_id)
    except Exception:
        pass

    return {"status": "deleted"}
