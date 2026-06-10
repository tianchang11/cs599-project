from app.db.repositories.base import BaseRepository
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.note_repo import NoteRepository
from app.db.repositories.task_repo import TaskRepository

user_repo = UserRepository()
note_repo = NoteRepository()
task_repo = TaskRepository()

__all__ = [
    "BaseRepository",
    "UserRepository",
    "NoteRepository",
    "TaskRepository",
    "user_repo",
    "note_repo",
    "task_repo",
]
