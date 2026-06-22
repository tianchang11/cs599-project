import pytest
from fastapi import HTTPException

import app.agents.tools  # noqa: F401
from app.agents.tools.executor import ToolExecutor
from app.agents.tools.visual import VisionAnalyzeTool
from app.api.routes.upload import upload_media
from app.core.config import settings
from app.services.multimodal_service import multimodal_analysis_service
from app.services.pdf_service import pdf_service


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


@pytest.mark.asyncio
async def test_upload_media_accepts_image(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_service, "upload_dir", tmp_path)

    response = await upload_media(FakeUploadFile("figure.png", b"\x89PNG\r\n"))

    assert response["mediaType"] == "image"
    assert response["filename"] == "figure.png"
    assert pdf_service.get_path(response["fileId"]).exists()


@pytest.mark.asyncio
async def test_upload_media_rejects_unsupported_type():
    with pytest.raises(HTTPException) as exc_info:
        await upload_media(FakeUploadFile("notes.exe", b"bad"))

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_image_upload_context_uses_mcp_visual_analysis(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_service, "upload_dir", tmp_path)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    file_id, media_type = pdf_service.save_media_file(b"\x89PNG\r\n", "figure.png")

    async def fake_analyze_image(path, api_key):
        return {
            "vision_analyze": {"summary": "chart about recycling", "objects": ["chart"], "safety_notes": []},
            "ocr_image": {"text": "plastic recycling rate", "confidence_notes": []},
        }

    monkeypatch.setattr(multimodal_analysis_service, "analyze_image", fake_analyze_image)

    context = await multimodal_analysis_service.build_uploaded_context_async(file_id)

    assert media_type == "image"
    assert "上传图片分析" in context
    assert "chart about recycling" in context
    assert "plastic recycling rate" in context


def test_tool_executor_registers_mcp_visual_tools():
    executor = ToolExecutor()

    assert "vision_analyze" in executor.tools
    assert "ocr_image" in executor.tools
    assert "audio_transcribe" in executor.tools
    assert "audio_summarize" in executor.tools
    assert "media_qa" in executor.tools


@pytest.mark.asyncio
async def test_vision_tool_returns_structured_result(monkeypatch):
    async def fake_run_visual_tool(tool_name, source, **kwargs):
        return {"summary": "visible result", "source": source}

    monkeypatch.setattr(multimodal_analysis_service, "run_visual_tool", fake_run_visual_tool)

    result = await VisionAnalyzeTool().execute(source={"type": "path", "value": "D:/media/photo.png"})

    assert result.success is True
    assert result.data["summary"] == "visible result"
