import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import StreamingResponse

from app.agents.graph import build_research_graph
from app.agents.strategies.base import get_strategy, STRATEGIES
from app.api.deps import get_user_context
from app.services.pdf_service import pdf_service
from app.schemas.research import ResearchStart, ResearchResponse, ResearchStatus
from app.tasks.manager import start_research_task, get_task_queue
from app.db.repositories import task_repo
from app.db.models import ResearchTask

logger = logging.getLogger(__name__)

router = APIRouter()


def sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    data: ResearchStart,
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-Id"),
    device_id: Optional[str] = Query(default=None),
):
    resolved_device_id = x_device_id or device_id or data.deviceId or "anonymous"
    user = await get_user_context(device_id=resolved_device_id)

    strategy_name = data.strategy
    if strategy_name and strategy_name not in STRATEGIES:
        raise HTTPException(status_code=422, detail=f"Invalid strategy. Available: {list(STRATEGIES.keys())}")

    task = await task_repo.create(
        user_id="temp",
        query=data.query,
        strategy=strategy_name or "analytical",
        status="pending",
        file_id=data.fileId,
    )

    asyncio.create_task(
        start_research_task(
            task_id=task.id,
            query=data.query,
            api_key=user.api_key,
            provider=user.provider,
            model=user.model,
            user_id="temp",
            file_id=data.fileId,
            strategy_name=strategy_name,
        )
    )

    return ResearchResponse(taskId=task.id, strategy=strategy_name or "analytical")


@router.get("/{task_id}/stream")
async def stream_research(task_id: str):
    queue = get_task_queue(task_id)

    if not queue:
        task = await task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status == "completed":
            return StreamingResponse(
                _replay_completed_task(task),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        elif task.status == "error":
            return StreamingResponse(
                iter([sse_event("error", {"error": task.error or "Task failed"})]),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache"},
            )
        else:
            queue = asyncio.Queue()
            from app.tasks.manager import _task_queues
            _task_queues[task_id] = queue

    return StreamingResponse(
        event_stream(task_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def event_stream(task_id: str, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=120.0)
        except asyncio.TimeoutError:
            task = await task_repo.get_by_id(task_id)
            if task and task.status in ("completed", "error"):
                break
            yield sse_event("step", {
                "step": "processing",
                "message": "仍在处理中...",
                "percent": 98,
            })
            continue

        event_type = item.get("type", "step")

        if event_type == "step":
            yield sse_event("step", {
                "step": item.get("step", ""),
                "message": item.get("message", ""),
                "percent": item.get("percent"),
            })
        elif event_type == "classified":
            yield sse_event("classified", {
                "category": item.get("category", ""),
                "confidence": item.get("confidence", 0),
            })
        elif event_type == "quality_update":
            yield sse_event("quality_update", {
                "qualityScore": item.get("quality_score", 0),
                "coverageScore": item.get("coverage_score", 0),
                "reportQuality": item.get("report_quality", 0),
                "iteration": item.get("iteration", 0),
                "draftIteration": item.get("draft_iteration", 0),
            })
        elif event_type == "done":
            task = await task_repo.get_by_id(task_id)
            if task and task.sources:
                sources = json.loads(task.sources) if isinstance(task.sources, str) else task.sources
                yield sse_event("sources", {"sources": sources})
            yield "data: [DONE]\n\n"
            break
        elif event_type == "error":
            yield sse_event("error", {"error": item.get("error", "Unknown error")})
            break


async def _replay_completed_task(task: ResearchTask) -> AsyncGenerator[str, None]:
    steps = json.loads(task.steps_log or "[]")
    for step in steps:
        yield sse_event("step", {
            "step": step.get("step", ""),
            "message": step.get("message", ""),
            "percent": step.get("percent"),
        })

    if task.report:
        yield sse_event("report", {"content": task.report})

    if task.sources:
        sources = json.loads(task.sources) if isinstance(task.sources, str) else task.sources
        yield sse_event("sources", {"sources": sources})

    yield "data: [DONE]\n\n"


@router.get("/{task_id}/report")
async def get_report(task_id: str):
    task = await task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == "pending":
        raise HTTPException(status_code=202, detail="Task is still pending")

    if task.status == "error":
        raise HTTPException(status_code=500, detail=task.error or "Task failed")

    sources = json.loads(task.sources) if task.sources else []

    return {
        "report": task.report or "",
        "sources": sources,
        "query": task.query,
        "strategy": task.strategy,
        "qualityScore": task.quality_score,
        "coverageScore": task.coverage_score,
        "reportQuality": task.report_quality,
        "iteration": task.iteration,
    }


@router.get("/{task_id}/status", response_model=ResearchStatus)
async def get_task_status(task_id: str):
    task = await task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return ResearchStatus(
        taskId=task.id,
        status=task.status,
        progress=task.progress,
        currentStep=task.current_step,
        strategy=task.strategy,
        qualityScore=task.quality_score,
        coverageScore=task.coverage_score,
        reportQuality=task.report_quality,
        iteration=task.iteration,
    )


@router.get("/strategies/available")
async def list_strategies():
    return {
        "strategies": [
            {"name": name, "description": get_strategy(name).description}
            for name in STRATEGIES.keys()
        ]
    }
