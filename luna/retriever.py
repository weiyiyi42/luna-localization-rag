"""Chroma-backed evidence retrieval for LUNA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from langchain_core.documents import Document

from luna.config import RetrievalConfig
from luna.embeddings import LunaEmbedder


@dataclass
class EvidenceResult:
    evidence_id: str
    text: str
    metadata: dict[str, Any]
    distance: float | None = None

    def to_document(self) -> Document:
        metadata = dict(self.metadata)
        metadata["evidence_id"] = self.evidence_id
        if self.distance is not None:
            metadata["distance"] = self.distance
        return Document(page_content=self.text, metadata=metadata)


class LunaRetriever:
    """Thin retriever over the local Chroma collection."""

    def __init__(
        self,
        db_dir: str | Path,
        collection_name: str,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.db_dir = Path(db_dir)
        self.collection_name = collection_name
        self.config = config or RetrievalConfig()
        self.embedder = LunaEmbedder(
            backend=self.config.embedding_backend,
            model_name=self.config.embedding_model,
            hash_dimensions=self.config.hash_dimensions,
        )
        self.client = chromadb.PersistentClient(path=str(self.db_dir))
        self.collection = self.client.get_collection(collection_name)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        source_type: str | None = None,
        min_trust_level: int | None = None,
    ) -> list[EvidenceResult]:
        where: dict[str, Any] = {}
        if source_type:
            where["source_type"] = source_type
        trust_floor = self.config.min_trust_level if min_trust_level is None else min_trust_level
        if trust_floor > 1:
            where["trust_level"] = {"$gte": trust_floor}

        result = self.collection.query(
            query_embeddings=[self.embedder.embed_query(query)],
            n_results=top_k or self.config.top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        output: list[EvidenceResult] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for idx, evidence_id in enumerate(ids):
            output.append(
                EvidenceResult(
                    evidence_id=evidence_id,
                    text=documents[idx],
                    metadata=metadatas[idx],
                    distance=distances[idx] if idx < len(distances) else None,
                )
            )
        return output

    def invoke(self, query: str) -> list[Document]:
        return [item.to_document() for item in self.search(query)]


def format_evidence(results: list[EvidenceResult], max_chars: int = 800) -> str:
    blocks: list[str] = []
    for idx, item in enumerate(results, start=1):
        source_type = item.metadata.get("source_type", "unknown")
        trust = item.metadata.get("trust_level", "n/a")
        preview = item.text[:max_chars]
        blocks.append(
            f"[{idx}] evidence_id={item.evidence_id} source={source_type} trust={trust}\n{preview}"
        )
    return "\n\n".join(blocks)

