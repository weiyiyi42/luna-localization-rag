"""Evaluation nodes for the LUNA graph.

The current implementation is a deterministic scaffold. It gives the project a
working graph and stable logs before a real LLM backend is connected.
"""

from __future__ import annotations

import re
from statistics import mean
from typing import Any

from luna.config import DeepSeekConfig
from luna.deepseek_client import DeepSeekClient
from luna.state import LunaState


def build_query(state: LunaState) -> dict:
    source = state.get("source_en", "")
    candidate = state.get("candidate_zh", "")
    return {"query": f"English source: {source}\nChinese candidate: {candidate}"}


def make_retrieve_node(retriever: LunaRetriever):
    def retrieve_evidence(state: LunaState) -> dict:
        query = state["query"]
        results = retriever.search(query)
        return {
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "text": item.text,
                    "metadata": item.metadata,
                    "distance": item.distance,
                }
                for item in results
            ]
        }

    return retrieve_evidence


def _evidence_ids(state: LunaState, limit: int = 4) -> list[str]:
    return [item["evidence_id"] for item in state.get("evidence", [])[:limit]]


def _contains_latin_term(text: str) -> bool:
    return bool(re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", text))


def _normalise_score_block(data: dict[str, Any], fallback_score: float) -> dict[str, Any]:
    if data.get("_parse_error"):
        return {
            "score": fallback_score,
            "explanation": "LLM response could not be parsed as valid JSON; fallback score used. Raw response preserved in raw_content.",
            "used_evidence_ids": [],
            "low_score_reasons": [],
            "evidence_feedback": [],
            "uncertainty_reasons": [],
            "improvement_suggestion": "",
            "parse_error": True,
            "raw_content": str(data.get("raw_content", ""))[:2000],
        }
    score = data.get("score", fallback_score)
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = fallback_score
    score = min(5.0, max(1.0, score))
    used_ids = data.get("used_evidence_ids", [])
    if not isinstance(used_ids, list):
        used_ids = []
    low_score_reasons = _string_list(data.get("low_score_reasons", []))
    evidence_feedback = _string_list(data.get("evidence_feedback", []))
    uncertainty_reasons = _string_list(data.get("uncertainty_reasons", []))
    return {
        "score": score,
        "explanation": str(data.get("explanation", "")).strip(),
        "used_evidence_ids": [str(item) for item in used_ids],
        "low_score_reasons": low_score_reasons,
        "evidence_feedback": evidence_feedback,
        "uncertainty_reasons": uncertainty_reasons,
        "improvement_suggestion": str(data.get("improvement_suggestion", "")).strip(),
        "parse_error": False,
    }


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _evidence_prompt(state: LunaState, limit: int = 8) -> str:
    blocks: list[str] = []
    for item in state.get("evidence", [])[:limit]:
        metadata = item.get("metadata", {})
        blocks.append(
            "\n".join(
                [
                    f"evidence_id: {item.get('evidence_id')}",
                    f"source_type: {metadata.get('source_type')}",
                    f"trust_level: {metadata.get('trust_level')}",
                    f"text: {item.get('text', '')[:900]}",
                ]
            )
        )
    return "\n\n---\n\n".join(blocks) if blocks else "No local evidence was retrieved."


def _preliminary_score_prompt(state: LunaState) -> str:
    if not all(key in state for key in ["meaning_score", "lore_score", "style_score"]):
        return "Preliminary scores are not available yet."
    return "\n".join(
        [
            f"meaning_score: {state['meaning_score'].get('score')}",
            f"lore_score: {state['lore_score'].get('score')}",
            f"style_score: {state['style_score'].get('score')}",
            f"uncertainty_variance: {state.get('uncertainty')}",
            f"route_reason: {state.get('route_reason')}",
        ]
    )


def _evaluation_user_prompt(state: LunaState, focus: str) -> str:
    return f"""
Evaluate one English-to-Simplified-Chinese game localization sample.

Focus: {focus}

English source:
{state.get("source_en", "")}

Chinese candidate:
{state.get("candidate_zh", "")}

Retrieved local evidence:
{_evidence_prompt(state)}

Preliminary routing context:
{_preliminary_score_prompt(state)}

Important evaluation rules:
- Evaluate this candidate on its own. Do not compare it against other translation versions.
- Do not assume a version is better because of its label, release order, or known historical status.
- Penalize unsupported additions, omitted meaning, misleading terminology, awkward Chinese, and lore inconsistency.
- Use retrieved evidence only when it is relevant. If retrieved evidence is weak, irrelevant, or ambiguous, say so.
- If the score is 3 or lower, explain which source meaning, translation issue, or database evidence caused the low score.
- If the judgement is uncertain, explain whether the uncertainty comes from ambiguous source wording, conflicting retrieved evidence, missing evidence, or weak retrieval.

Return only JSON with this schema:
{{
  "score": 1-5,
  "explanation": "short evidence-based explanation",
  "used_evidence_ids": ["evidence ids actually used"],
  "low_score_reasons": ["only fill when score <= 3 or there is a serious issue"],
  "evidence_feedback": ["for each important evidence item, explain how it supports, contradicts, or fails to support the candidate"],
  "uncertainty_reasons": ["explain why the score is uncertain; empty if judgement is confident"],
  "improvement_suggestion": "short suggestion if the translation is weak; otherwise empty"
}}
"""


def _llm_score(
    client: DeepSeekClient,
    model: str,
    state: LunaState,
    focus: str,
    fallback_score: float,
    thinking_enabled: bool = False,
) -> dict[str, Any]:
    system = (
        "You are LUNA, a careful localization quality evaluator. "
        "Use retrieved evidence only when it is relevant. "
        "Do not invent lore facts. Return valid JSON only."
    )
    response = client.chat_json(
        model=model,
        system=system,
        user=_evaluation_user_prompt(state, focus),
        thinking_enabled=thinking_enabled,
    )
    block = _normalise_score_block(response.parsed, fallback_score)
    block["model"] = response.model
    block["usage"] = response.usage
    return block


def heuristic_meaning_agent(state: LunaState) -> dict:
    source = state.get("source_en", "")
    candidate = state.get("candidate_zh", "")
    score = 4.0
    if not candidate.strip():
        score = 1.0
    elif len(candidate) < max(2, len(source) * 0.08):
        score = 2.5
    return {
        "meaning_score": {
            "score": score,
            "explanation": "Heuristic scaffold: checks for empty or very short candidate text.",
            "used_evidence_ids": [],
        }
    }


def heuristic_lore_agent(state: LunaState) -> dict:
    evidence = state.get("evidence", [])
    trusted = [item for item in evidence if int(item.get("metadata", {}).get("trust_level", 0)) >= 2]
    score = 4.0 if trusted else 2.5
    used = [item["evidence_id"] for item in trusted[:4]]
    return {
        "lore_score": {
            "score": score,
            "explanation": "Heuristic scaffold: rewards availability of trusted local evidence.",
            "used_evidence_ids": used,
        }
    }


def heuristic_style_agent(state: LunaState) -> dict:
    candidate = state.get("candidate_zh", "")
    score = 4.0
    if _contains_latin_term(candidate):
        score = 3.2
    if len(candidate) > 120:
        score -= 0.4
    return {
        "style_score": {
            "score": max(1.0, score),
            "explanation": "Heuristic scaffold: flags long text and untranslated Latin-script terms.",
            "used_evidence_ids": [],
        }
    }


def make_meaning_agent(client: DeepSeekClient | None, config: DeepSeekConfig):
    def meaning_agent(state: LunaState) -> dict:
        if client is None:
            return heuristic_meaning_agent(state)
        return {
            "meaning_score": _llm_score(
                client,
                config.preliminary_model,
                state,
                "meaning accuracy: whether the Chinese candidate preserves the English source meaning.",
                fallback_score=3.0,
            )
        }

    return meaning_agent


def make_lore_agent(client: DeepSeekClient | None, config: DeepSeekConfig):
    def lore_agent(state: LunaState) -> dict:
        if client is None:
            return heuristic_lore_agent(state)
        return {
            "lore_score": _llm_score(
                client,
                config.preliminary_model,
                state,
                "lore and terminology: whether names, terms, and game-world facts are consistent with evidence.",
                fallback_score=3.0,
            )
        }

    return lore_agent


def make_style_agent(client: DeepSeekClient | None, config: DeepSeekConfig):
    def style_agent(state: LunaState) -> dict:
        if client is None:
            return heuristic_style_agent(state)
        return {
            "style_score": _llm_score(
                client,
                config.preliminary_model,
                state,
                "style and readability: whether the Chinese reads naturally and fits the tone of game text.",
                fallback_score=3.0,
            )
        }

    return style_agent


def make_compute_uncertainty(
    threshold: float = 0.45,
    low_score_threshold: float = 2.0,
    low_average_threshold: float = 2.5,
):
    def compute_uncertainty(state: LunaState) -> dict:
        scores = [
            state["meaning_score"]["score"],
            state["lore_score"]["score"],
            state["style_score"]["score"],
        ]
        avg = mean(scores)
        min_score = min(scores)
        variance = sum((score - avg) ** 2 for score in scores) / len(scores)
        if variance > threshold:
            route = "deep_audit"
            route_reason = "high_uncertainty"
        elif min_score <= low_score_threshold:
            route = "deep_audit"
            route_reason = "low_dimension_score"
        elif avg <= low_average_threshold:
            route = "deep_audit"
            route_reason = "low_average_score"
        else:
            route = "finalize"
            route_reason = "fast_path"
        return {
            "uncertainty": variance,
            "route": route,
            "route_reason": route_reason,
            "routing_threshold": threshold,
            "low_score_threshold": low_score_threshold,
            "low_average_threshold": low_average_threshold,
            "preliminary_mean_score": avg,
            "preliminary_min_score": min_score,
        }

    return compute_uncertainty


def route_by_uncertainty(state: LunaState) -> str:
    return state.get("route", "finalize")


def make_deep_audit_agent(client: DeepSeekClient | None, config: DeepSeekConfig):
    def deep_audit_agent(state: LunaState) -> dict:
        if client is not None:
            return {
                "deep_audit": _llm_score(
                    client,
                    config.deep_audit_model,
                    state,
                    "deep audit: resolve uncertainty or low-score risk from the preliminary agents and produce a more careful judgement.",
                    fallback_score=mean(
                        [
                            state["meaning_score"]["score"],
                            state["lore_score"]["score"],
                            state["style_score"]["score"],
                        ]
                    ),
                    thinking_enabled=True,
                )
            }
        used = _evidence_ids(state, limit=6)
        return {
            "deep_audit": {
                "score": mean(
                    [
                        state["meaning_score"]["score"],
                        state["lore_score"]["score"],
                        state["style_score"]["score"],
                    ]
                ),
                "explanation": "Deep-audit placeholder reached because routing detected uncertainty or low-score risk.",
                "used_evidence_ids": used,
            }
        }

    return deep_audit_agent


def final_synthesizer(state: LunaState) -> dict:
    scores = {
        "meaning_accuracy": state["meaning_score"],
        "lore_and_terminology": state["lore_score"],
        "style_and_readability": state["style_score"],
    }
    if "deep_audit" in state:
        scores["deep_audit"] = state["deep_audit"]
    numeric = [block["score"] for block in scores.values() if "score" in block]
    overall = round(mean(numeric), 2) if numeric else 0.0
    used_ids: list[str] = []
    low_score_reasons: list[str] = []
    evidence_feedback: list[str] = []
    uncertainty_reasons: list[str] = []
    for block in scores.values():
        used_ids.extend(block.get("used_evidence_ids", []))
        low_score_reasons.extend(block.get("low_score_reasons", []))
        evidence_feedback.extend(block.get("evidence_feedback", []))
        uncertainty_reasons.extend(block.get("uncertainty_reasons", []))
    used_ids = list(dict.fromkeys(used_ids))
    low_score_reasons = list(dict.fromkeys(low_score_reasons))
    evidence_feedback = list(dict.fromkeys(evidence_feedback))
    uncertainty_reasons = list(dict.fromkeys(uncertainty_reasons))
    return {
        "final_report": {
            "sample_id": state.get("sample_id"),
            "overall_score": overall,
            "dimension_scores": scores,
            "evidence_ids": used_ids,
            "low_score_reasons": low_score_reasons,
            "evidence_feedback": evidence_feedback,
            "uncertainty_reasons": uncertainty_reasons,
            "route": state.get("route", "finalize"),
            "route_reason": state.get("route_reason", "fast_path"),
            "uncertainty": state.get("uncertainty", 0.0),
            "preliminary_mean_score": state.get("preliminary_mean_score"),
            "preliminary_min_score": state.get("preliminary_min_score"),
            "routing_threshold": state.get("routing_threshold"),
            "low_score_threshold": state.get("low_score_threshold"),
            "low_average_threshold": state.get("low_average_threshold"),
            "explanation": "Report generated by the LUNA LangGraph pipeline.",
        }
    }
