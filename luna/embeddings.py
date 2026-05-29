"""Embedding helpers shared by LUNA indexing and querying."""

from __future__ import annotations

import hashlib
import math
import re


def tokenise(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_']+|[\u4e00-\u9fff]", text.lower())


def hash_embeddings(texts: list[str], dimensions: int = 1024) -> list[list[float]]:
    """Deterministic local embedding for offline smoke tests.

    This is not the thesis-grade retrieval model. Use BGE-M3 for formal runs.
    """

    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * dimensions
        for token in tokenise(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % dimensions
            sign = 1.0 if (value >> 63) == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        vectors.append([v / norm for v in vector])
    return vectors


class LunaEmbedder:
    """Small embedding adapter with the same methods LangChain expects."""

    def __init__(
        self,
        backend: str = "hash",
        model_name: str = "BAAI/bge-m3",
        hash_dimensions: int = 1024,
    ) -> None:
        self.backend = backend
        self.model_name = model_name
        self.hash_dimensions = hash_dimensions
        self._model = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.backend == "hash":
            return hash_embeddings(texts, self.hash_dimensions)
        if self.backend == "bge-m3":
            return self._embed_bge_m3(texts)
        raise ValueError(f"Unsupported embedding backend: {self.backend}")

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _embed_bge_m3(self, texts: list[str]) -> list[list[float]]:
        from sentence_transformers import SentenceTransformer

        if self._model is None:
            self._model = SentenceTransformer(self.model_name, trust_remote_code=True)
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

