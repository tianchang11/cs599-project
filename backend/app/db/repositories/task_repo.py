import json
from typing import Optional

from sqlalchemy import select

from app.db.models import ResearchTask
from app.db.repositories.base import BaseRepository


class TaskRepository(BaseRepository[ResearchTask]):
    model = ResearchTask

    async def get_by_user_id(self, user_id: str, limit: int = 20) -> list[ResearchTask]:
        from app.db.database import async_session
        async with async_session() as session:
            result = await session.execute(
                select(ResearchTask)
                .where(ResearchTask.user_id == user_id)
                .order_by(ResearchTask.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def update_progress(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        step_entry: Optional[dict] = None,
        report: Optional[str] = None,
        sources: Optional[list] = None,
        error: Optional[str] = None,
        iteration: Optional[int] = None,
        quality_score: Optional[float] = None,
        coverage_score: Optional[float] = None,
        report_quality: Optional[float] = None,
    ) -> Optional[ResearchTask]:
        from app.db.database import async_session
        async with async_session() as session:
            result = await session.execute(select(ResearchTask).where(ResearchTask.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                return None

            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if current_step is not None:
                task.current_step = current_step
            if step_entry is not None:
                steps = json.loads(task.steps_log or "[]")
                steps.append(step_entry)
                task.steps_log = json.dumps(steps)
            if report is not None:
                task.report = report
            if sources is not None:
                task.sources = json.dumps(sources)
            if error is not None:
                task.error = error
            if iteration is not None:
                task.iteration = iteration
            if quality_score is not None:
                task.quality_score = quality_score
            if coverage_score is not None:
                task.coverage_score = coverage_score
            if report_quality is not None:
                task.report_quality = report_quality

            await session.commit()
            await session.refresh(task)
            return task
