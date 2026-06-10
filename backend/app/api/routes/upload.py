import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.pdf_service import pdf_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    try:
        file_id = pdf_service.save_file(content, file.filename)
        logger.info(f"Uploaded PDF: {file_id} ({file.filename}, {len(content)} bytes)")
        return {"fileId": file_id, "filename": file.filename, "size": len(content)}
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
