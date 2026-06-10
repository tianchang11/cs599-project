import logging
import uuid
import hashlib
from pathlib import Path
from typing import TypedDict

import fitz  # PyMuPDF

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFChunk(TypedDict):
    id: str
    text: str
    page: int


class PDFService:
    def __init__(self, upload_dir: Path | None = None):
        self.upload_dir = upload_dir or settings.upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, content: bytes, filename: str) -> str:
        file_id = uuid.uuid4().hex
        ext = Path(filename).suffix.lower()
        path = self.upload_dir / f"{file_id}{ext}"
        path.write_bytes(content)
        return file_id

    def get_path(self, file_id: str) -> Path | None:
        for ext in [".pdf", ".txt"]:
            path = self.upload_dir / f"{file_id}{ext}"
            if path.exists():
                return path
        return None

    def extract_text(self, file_id: str) -> str:
        path = self.get_path(file_id)
        if not path:
            raise FileNotFoundError(f"File {file_id} not found")

        if path.suffix == ".txt":
            return path.read_text(encoding="utf-8")

        text_parts = []
        try:
            doc = fitz.open(str(path))
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_id}: {e}")
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

        return "\n\n".join(text_parts)

    def chunk_text(self, text: str, chunk_size: int = 512) -> list[PDFChunk]:
        """Split text into semantic chunks of ~chunk_size tokens (roughly chars / 4)."""
        char_limit = chunk_size * 4
        chunks: list[PDFChunk] = []
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            if len(current) + len(para) < char_limit:
                current += "\n\n" + para
            else:
                if current.strip():
                    chunks.append(PDFChunk(
                        id=hashlib.md5(current.encode()).hexdigest()[:16],
                        text=current.strip(),
                        page=0,
                    ))
                current = para

        if current.strip():
            chunks.append(PDFChunk(
                id=hashlib.md5(current.encode()).hexdigest()[:16],
                text=current.strip(),
                page=0,
            ))

        return chunks


pdf_service = PDFService()
