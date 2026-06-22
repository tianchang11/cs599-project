from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from multimodal_mcp.config import Settings
from multimodal_mcp.media import MediaArtifact


class OpenAIProvider:
    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        self.settings = settings
        self.client = client or AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)

    async def analyze_image(self, artifact: MediaArtifact, prompt: str, detail: str = "auto") -> dict[str, Any]:
        data_url = _image_data_url(artifact.path, artifact.mime_type)
        response = await self.client.responses.create(
            model=self.settings.openai_vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url, "detail": detail},
                    ],
                }
            ],
        )
        return _parse_json_or_text(_response_text(response), fallback_key="raw_answer")

    async def transcribe_audio(
        self,
        artifact: MediaArtifact,
        language: str | None = None,
        timestamps: bool = False,
        diarize: bool = False,
    ) -> dict[str, Any]:
        model = self.settings.openai_diarize_model if diarize else self.settings.openai_transcribe_model
        kwargs: dict[str, Any] = {"model": model, "file": artifact.path.open("rb")}
        if language:
            kwargs["language"] = language
        if timestamps:
            kwargs["response_format"] = "verbose_json"
            kwargs["timestamp_granularities"] = ["segment"]

        try:
            response = await self.client.audio.transcriptions.create(**kwargs)
        finally:
            kwargs["file"].close()

        return _model_dump(response)

    async def summarize_text(self, transcript: str, summary_style: str, language: str | None = None) -> dict[str, Any]:
        language_hint = f" Use {language} for the summary." if language else ""
        prompt = (
            "Summarize this transcript as JSON with keys summary, key_points, and action_items. "
            f"Style: {summary_style}.{language_hint}\n\nTranscript:\n{transcript}"
        )
        response = await self.client.responses.create(
            model=self.settings.openai_summary_model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        )
        return _parse_json_or_text(_response_text(response), fallback_key="summary")

    async def answer_text_question(self, context: str, question: str) -> dict[str, Any]:
        prompt = (
            "Answer the user question using only the provided transcript/context. "
            "Return JSON with keys answer, evidence, and intermediate_summary.\n\n"
            f"Question: {question}\n\nContext:\n{context}"
        )
        response = await self.client.responses.create(
            model=self.settings.openai_summary_model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        )
        return _parse_json_or_text(_response_text(response), fallback_key="answer")


def _image_data_url(path: Path, mime_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)
    dumped = _model_dump(response)
    return json.dumps(dumped, ensure_ascii=False)


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {"text": str(value)}


def _parse_json_or_text(text: str, fallback_key: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```json"):
        stripped = stripped.removeprefix("```json").removesuffix("```").strip()
    elif stripped.startswith("```"):
        stripped = stripped.removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {fallback_key: text}

