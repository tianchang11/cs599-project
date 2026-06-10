import asyncio
import json
import logging
from typing import Any, Optional

from app.agents.graph import build_research_graph
from app.agents.router import strategy_router
from app.agents.strategies.base import get_strategy
from app.agents.adaptive import AdaptiveDepthController
from app.db.repositories import task_repo
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)

_task_queues: dict[str, asyncio.Queue] = {}


async def start_research_task(
    task_id: str,
    query: str,
    api_key: str,
    provider: str,
    model: str,
    user_id: str,
    file_id: str | None = None,
    strategy_name: str | None = None,
) -> None:
    _task_queues[task_id] = asyncio.Queue()

    try:
        await task_repo.update_progress(task_id, status="running", current_step="initializing")

        if strategy_name is None:
            strategy, category, confidence = await strategy_router.route(
                query=query,
                api_key=api_key,
                provider=provider,
                model=model,
                user_id=user_id,
            )
            strategy_name = category
            await _emit_event(task_id, {
                "type": "classified",
                "category": category,
                "confidence": confidence,
            })
        else:
            strategy = get_strategy(strategy_name)

        adaptive_ctrl = AdaptiveDepthController()
        depth_config = adaptive_ctrl.compute_initial_depth(
            query=query,
            category=strategy.name,
            confidence=1.0 if strategy_name else 0.5,
        )

        pdf_context = ""
        if file_id:
            try:
                raw_text = pdf_service.extract_text(file_id)
                pdf_context = f"\n\n[上传的文档内容]:\n{raw_text[:4000]}"
                logger.info(f"[Research {task_id}] Loaded PDF: {len(raw_text)} chars")
            except Exception as e:
                logger.warning(f"[Research {task_id}] PDF load failed: {e}")

        state: dict[str, Any] = {
            "query": query,
            "api_key": api_key,
            "provider": provider,
            "model": model,
            "pdf_context": pdf_context,
            "sub_queries": [],
            "search_results": {},
            "filtered_content": {},
            "synthesis_text": "",
            "report": "",
            "sources": [],
            "current_step": "planning",
            "steps": [],
            "iteration": 0,
            "draft_iteration": 0,
            "quality_score": 0.0,
            "coverage_score": 0.0,
            "report_quality": 0.0,
            "needs_refinement": False,
            "needs_more_research": False,
            "needs_revision": False,
            "refinement_suggestions": [],
            "missing_aspects": [],
            "revision_suggestions": [],
            "quality_threshold": strategy.quality_threshold,
            "coverage_threshold": strategy.coverage_threshold,
            "report_quality_threshold": strategy.report_quality_threshold,
            "max_sub_queries": depth_config["sub_queries_count"],
            "search_depth": depth_config["search_depth"],
            "strategy_name": strategy.name,
            "_previous_quality": None,
            "_previous_coverage": None,
            "should_continue_iteration": True,
            "termination_reason": None,
        }

        graph = build_research_graph(strategy)

        prev_quality = 0.0
        prev_coverage = 0.0
        prev_report_quality = 0.0

        async for chunk in graph.astream(state):
            for node_name, node_state in chunk.items():
                if node_state != state:
                    state = node_state

                    new_steps = node_state.get("steps", [])
                    if new_steps:
                        latest = new_steps[-1]
                        await _emit_event(task_id, {
                            "type": "step",
                            "step": latest["step"],
                            "message": latest.get("message", ""),
                            "percent": latest.get("percent"),
                        })

                    cur_quality = state.get("quality_score", 0.0)
                    cur_coverage = state.get("coverage_score", 0.0)
                    cur_report_quality = state.get("report_quality", 0.0)

                    if cur_quality != prev_quality or cur_coverage != prev_coverage or cur_report_quality != prev_report_quality:
                        await _emit_event(task_id, {
                            "type": "quality_update",
                            "quality_score": cur_quality,
                            "coverage_score": cur_coverage,
                            "report_quality": cur_report_quality,
                            "iteration": state.get("iteration", 0),
                            "draft_iteration": state.get("draft_iteration", 0),
                        })
                        prev_quality = cur_quality
                        prev_coverage = cur_coverage
                        prev_report_quality = cur_report_quality

                    await task_repo.update_progress(
                        task_id,
                        current_step=state.get("current_step", "planning"),
                        progress=state.get("steps", [{}])[-1].get("percent", 0) if state.get("steps") else 0,
                        step_entry=state.get("steps", [{}])[-1] if state.get("steps") else None,
                        iteration=state.get("iteration", 0),
                        quality_score=cur_quality,
                        coverage_score=cur_coverage,
                        report_quality=cur_report_quality,
                    )

        report = state.get("report", "")
        sources = state.get("sources", [])

        await task_repo.update_progress(
            task_id,
            status="completed",
            progress=100,
            current_step="done",
            report=report,
            sources=sources,
        )

        await _emit_event(task_id, {"type": "done"})

    except Exception as e:
        logger.exception(f"[Research {task_id}] Error: {e}")
        await task_repo.update_progress(task_id, status="error", error=str(e))
        await _emit_event(task_id, {"type": "error", "error": str(e)})
    finally:
        _task_queues.pop(task_id, None)


async def _emit_event(task_id: str, event: dict) -> None:
    queue = _task_queues.get(task_id)
    if queue:
        await queue.put(event)


def get_task_queue(task_id: str) -> Optional[asyncio.Queue]:
    return _task_queues.get(task_id)
