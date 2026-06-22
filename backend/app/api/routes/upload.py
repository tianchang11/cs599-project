import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.services.pdf_service import SUPPORTED_MEDIA_EXTENSIONS, pdf_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {settings.max_file_size_mb}MB limit")

    try:
        file_id = pdf_service.save_file(content, file.filename)
        logger.info(f"Uploaded PDF: {file_id} ({file.filename}, {len(content)} bytes)")
        return {"fileId": file_id, "filename": file.filename, "size": len(content), "mediaType": "pdf"}
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")


@router.post("/media")
async def upload_media(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in SUPPORTED_MEDIA_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, image, and audio files are supported")

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {settings.max_file_size_mb}MB limit")

    try:
        file_id, media_type = pdf_service.save_media_file(content, file.filename)
        logger.info(
            "Uploaded media: %s (%s, %s, %d bytes)",
            file_id,
            file.filename,
            media_type,
            len(content),
        )
        return {"fileId": file_id, "filename": file.filename, "size": len(content), "mediaType": media_type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Media upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
