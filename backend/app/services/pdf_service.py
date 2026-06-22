import logging
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Literal, TypedDict

import fitz  # PyMuPDF

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFChunk(TypedDict):
    id: str
    text: str
    page: int


MediaType = Literal["pdf", "image", "audio"]


SUPPORTED_MEDIA_EXTENSIONS: dict[str, MediaType] = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".mpeg": "audio",
    ".mpga": "audio",
    ".ogg": "audio",
    ".oga": "audio",
    ".flac": "audio",
}


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

    def save_media_file(self, content: bytes, filename: str) -> tuple[str, MediaType]:
        ext = Path(filename).suffix.lower()
        media_type = SUPPORTED_MEDIA_EXTENSIONS.get(ext)
        if not media_type:
            raise ValueError("Unsupported media type")
        file_id = self.save_file(content, filename)
        return file_id, media_type

    def get_path(self, file_id: str) -> Path | None:
        for ext in [".pdf", ".txt", *SUPPORTED_MEDIA_EXTENSIONS.keys()]:
            path = self.upload_dir / f"{file_id}{ext}"
            if path.exists():
                return path
        return None

    def get_media_type(self, file_id: str) -> MediaType | None:
        path = self.get_path(file_id)
        if not path:
            return None
        if path.suffix == ".txt":
            return "pdf"
        return SUPPORTED_MEDIA_EXTENSIONS.get(path.suffix.lower())

    def get_mime_type(self, file_id: str) -> str | None:
        path = self.get_path(file_id)
        if not path:
            return None
        guessed, _ = mimetypes.guess_type(path.name)
        return guessed

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
