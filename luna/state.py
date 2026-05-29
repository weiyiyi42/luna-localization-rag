"""State schema for the LUNA LangGraph workflow."""

from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class ScoreBlock(TypedDict, total=False):
    score: float
    explanation: str
    used_evidence_ids: list[str]
    low_score_reasons: list[str]
    evidence_feedback: list[str]
    uncertainty_reasons: list[str]
    improvement_suggestion: str


class LunaState(TypedDict, total=False):
    sample_id: str
    source_en: str
    candidate_zh: str
    version_code: str
    version_label: str
    query: str
    evidence: list[dict[str, Any]]
    meaning_score: ScoreBlock
    lore_score: ScoreBlock
    style_score: ScoreBlock
    deep_audit: ScoreBlock
    uncertainty: float
    routing_threshold: float
    low_score_threshold: float
    low_average_threshold: float
    preliminary_mean_score: float
    preliminary_min_score: float
    route_reason: str
    route: str
    final_report: dict[str, Any]
