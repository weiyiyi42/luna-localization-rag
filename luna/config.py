"""Configuration defaults for the LUNA local RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class LunaPaths:
    vector_db_dir: Path = Path("data/vector_db/luna_lore_chroma")
    collection_name: str = "luna_lore_evidence"
    knowledge_base_dir: Path = Path("data/processed/luna_knowledge_base")
    evidence_jsonl: Path = Path("data/processed/luna_knowledge_base/evidence.jsonl")
    terminology_jsonl: Path = Path("data/processed/luna_knowledge_base/terminology.jsonl")
    run_log_dir: Path = Path("data/processed/luna_runs")


@dataclass(frozen=True)
class RetrievalConfig:
    embedding_backend: str = "hash"
    embedding_model: str = "BAAI/bge-m3"
    hash_dimensions: int = 1024
    top_k: int = 8
    fetch_k: int = 24
    min_trust_level: int = 1


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key_env: str = "DEEPSEEK_API_KEY"
    base_url: str = "https://api.deepseek.com"
    preliminary_model: str = "deepseek-v4-flash"
    deep_audit_model: str = "deepseek-v4-pro"
    final_model: str = "deepseek-v4-flash"
    max_tokens: int = 1200
    temperature: float = 0.0
    use_llm: bool = True
    routing_threshold: float = 0.45
    low_score_threshold: float = 2.0
    low_average_threshold: float = 2.5

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)
