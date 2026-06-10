import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "research_notes"


class VectorService:
    def __init__(self, host: str | None = None, port: int | None = None):
        self.host = host or settings.chroma_host
        self.port = port or settings.chroma_port
        self._client: Optional[chromadb.ClientAPI] = None
        self._embedding_provider: Optional[str] = None

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            try:
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._client.heartbeat()
                logger.info(f"Connected to Chroma at {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"Failed to connect to remote Chroma: {e}, falling back to in-memory")
                self._client = chromadb.Client(ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ))
        return self._client

    def get_or_create_collection(self, name: str = COLLECTION_NAME):
        return self.client.get_or_create_collection(
            name=name,
            metadata={"description": "DeepResearch Agent notes collection"},
        )

    def add_note(self, note_id: str, text: str, user_id: str, title: str, metadata: dict | None = None):
        collection = self.get_or_create_collection()
        embedding = self._get_embedding(text)
        collection.add(
            ids=[note_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "user_id": user_id,
                "title": title,
                **(metadata or {}),
            }],
        )

    def search_notes(self, query: str, user_id: str, top_k: int = 5) -> list[dict]:
        collection = self.get_or_create_collection()
        query_embedding = self._get_embedding(query)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"user_id": user_id},
            )
        except Exception as e:
            logger.warning(f"Vector search with filter failed: {e}, trying without filter")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

        hits = []
        if results and results.get("ids") and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                hits.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if results.get("documents") else "",
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else None,
                })
        return hits

    def delete_note(self, note_id: str):
        collection = self.get_or_create_collection()
        try:
            collection.delete(ids=[note_id])
        except Exception as e:
            logger.warning(f"Failed to delete note {note_id} from vector store: {e}")

    def _get_embedding(self, text: str) -> list[float]:
        embedding = self._try_openai_embedding(text)
        if embedding:
            return embedding

        embedding = self._try_local_embedding(text)
        if embedding:
            return embedding

        return self._fallback_embedding(text)

    def _try_openai_embedding(self, text: str) -> Optional[list[float]]:
        try:
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                return None

            import httpx
            client = httpx.Client(timeout=15.0)
            resp = client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-3-small", "input": text[:8000]},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.debug(f"OpenAI embedding failed: {e}")
        return None

    def _try_local_embedding(self, text: str) -> Optional[list[float]]:
        try:
            import httpx
            resp = httpx.post(
                f"http://{self.host}:{self.port}/api/v1/embeddings",
                json={"model": "BAAI/bge-m3", "input": text[:2048]},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()["data"][0]["embedding"]
        except Exception:
            pass
        return None

    def _fallback_embedding(self, text: str) -> list[float]:
        import hashlib
        import struct
        h = hashlib.sha256(text.encode()).digest()
        return list(struct.unpack(f"{len(h) // 4}f", h))


vector_service = VectorService()
