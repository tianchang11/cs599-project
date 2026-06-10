import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:12]}"
    )
    device_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_key_iv: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    notes: Mapped[list["Note"]] = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list["ResearchTask"]] = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: f"note_{uuid.uuid4().hex[:12]}"
    )
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[str] = mapped_column(Text, default="[]")
    query: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="notes")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:12]}"
    )
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(Text)
    strategy: Mapped[str] = mapped_column(String(50), default="analytical")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    steps_log: Mapped[Optional[str]] = mapped_column(Text, default="[]")
    report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[Optional[str]] = mapped_column(Text, default="[]")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coverage_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    report_quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")
