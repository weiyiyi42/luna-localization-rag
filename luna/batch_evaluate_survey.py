"""Batch-evaluate survey localization samples with the LUNA graph."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from luna.config import DeepSeekConfig, LunaPaths, RetrievalConfig
from luna.graph import build_luna_graph


DEFAULT_SURVEY_CSV = Path("data/survey/survey_items_100.csv")
DEFAULT_OUT_DIR = Path("data/processed/luna_runs/survey_eval")
VERSION_COLUMNS = [
    ("V1", "V1_label", "V1_zh"),
    ("V2", "V2_label", "V2_zh"),
    ("V3", "V3_label", "V3_zh"),
]


def read_survey_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if limit is not None:
        rows = rows[:limit]
    return rows


def flatten_report(
    *,
    item: dict[str, str],
    version_code: str,
    version_label: str,
    candidate_zh: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    dimensions = report.get("dimension_scores", {})
    meaning = dimensions.get("meaning_accuracy", {})
    lore = dimensions.get("lore_and_terminology", {})
    style = dimensions.get("style_and_readability", {})
    deep = dimensions.get("deep_audit", {})
    return {
        "sample_id": report.get("sample_id", ""),
        "item_id": item.get("item_id", ""),
        "source_type": item.get("source_type", ""),
        "key": item.get("key", ""),
        "length_bucket": item.get("length_bucket", ""),
        "version_code": version_code,
        "version_label": version_label,
        "english": item.get("english", ""),
        "candidate_zh": candidate_zh,
        "overall_score": report.get("overall_score", ""),
        "meaning_score": meaning.get("score", ""),
        "lore_score": lore.get("score", ""),
        "style_score": style.get("score", ""),
        "deep_audit_score": deep.get("score", ""),
        "route": report.get("route", ""),
        "route_reason": report.get("route_reason", ""),
        "uncertainty": report.get("uncertainty", ""),
        "preliminary_mean_score": report.get("preliminary_mean_score", ""),
        "preliminary_min_score": report.get("preliminary_min_score", ""),
        "routing_threshold": report.get("routing_threshold", ""),
        "low_score_threshold": report.get("low_score_threshold", ""),
        "low_average_threshold": report.get("low_average_threshold", ""),
        "evidence_ids": "; ".join(report.get("evidence_ids", [])),
        "final_low_score_reasons": "; ".join(report.get("low_score_reasons", [])),
        "final_evidence_feedback": "; ".join(report.get("evidence_feedback", [])),
        "final_uncertainty_reasons": "; ".join(report.get("uncertainty_reasons", [])),
        "meaning_explanation": meaning.get("explanation", ""),
        "lore_explanation": lore.get("explanation", ""),
        "style_explanation": style.get("explanation", ""),
        "deep_audit_explanation": deep.get("explanation", ""),
        "meaning_low_score_reasons": "; ".join(meaning.get("low_score_reasons", [])),
        "lore_low_score_reasons": "; ".join(lore.get("low_score_reasons", [])),
        "style_low_score_reasons": "; ".join(style.get("low_score_reasons", [])),
        "deep_audit_low_score_reasons": "; ".join(deep.get("low_score_reasons", [])),
        "meaning_evidence_feedback": "; ".join(meaning.get("evidence_feedback", [])),
        "lore_evidence_feedback": "; ".join(lore.get("evidence_feedback", [])),
        "style_evidence_feedback": "; ".join(style.get("evidence_feedback", [])),
        "deep_audit_evidence_feedback": "; ".join(deep.get("evidence_feedback", [])),
        "meaning_uncertainty_reasons": "; ".join(meaning.get("uncertainty_reasons", [])),
        "lore_uncertainty_reasons": "; ".join(lore.get("uncertainty_reasons", [])),
        "style_uncertainty_reasons": "; ".join(style.get("uncertainty_reasons", [])),
        "deep_audit_uncertainty_reasons": "; ".join(deep.get("uncertainty_reasons", [])),
        "meaning_improvement_suggestion": meaning.get("improvement_suggestion", ""),
        "lore_improvement_suggestion": lore.get("improvement_suggestion", ""),
        "style_improvement_suggestion": style.get("improvement_suggestion", ""),
        "deep_audit_improvement_suggestion": deep.get("improvement_suggestion", ""),
        "parse_error": any(
            bool(block.get("parse_error"))
            for block in [meaning, lore, style, deep]
            if isinstance(block, dict)
        ),
        "error": report.get("error", ""),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--survey-csv", type=Path, default=DEFAULT_SURVEY_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit", type=int, help="Evaluate only the first N survey rows.")
    parser.add_argument("--versions", default="V1,V2,V3", help="Comma-separated version codes.")
    parser.add_argument("--embedding-backend", choices=["hash", "bge-m3"], default="hash")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic scaffold nodes.")
    parser.add_argument("--no-rag", action="store_true", help="Do not retrieve local evidence.")
    parser.add_argument("--routing-threshold", type=float, default=0.45)
    parser.add_argument("--low-score-threshold", type=float, default=2.0)
    parser.add_argument("--low-average-threshold", type=float, default=2.5)
    parser.add_argument("--preliminary-model", default="deepseek-v4-flash")
    parser.add_argument("--deep-audit-model", default="deepseek-v4-pro")
    parser.add_argument("--run-name", default=None)
    args = parser.parse_args()

    selected_versions = {part.strip() for part in args.versions.split(",") if part.strip()}
    run_name = args.run_name or datetime.now(timezone.utc).strftime("survey_%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    deepseek_config = DeepSeekConfig(
        preliminary_model=args.preliminary_model,
        deep_audit_model=args.deep_audit_model,
        use_llm=not args.no_llm,
        routing_threshold=args.routing_threshold,
        low_score_threshold=args.low_score_threshold,
        low_average_threshold=args.low_average_threshold,
    )
    llm_client_active = deepseek_config.use_llm and bool(deepseek_config.api_key)
    if deepseek_config.use_llm and not llm_client_active:
        raise SystemExit(
            f"DeepSeek LLM mode is enabled, but {deepseek_config.api_key_env} is not set. "
            "Set it in this PowerShell session, or add --no-llm if this is only a scaffold smoke test."
        )

    graph = build_luna_graph(
        LunaPaths(),
        RetrievalConfig(embedding_backend=args.embedding_backend),
        deepseek_config,
        use_retrieval=not args.no_rag,
    )
    survey_rows = read_survey_rows(args.survey_csv, args.limit)
    flat_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []

    total = len(survey_rows) * len(selected_versions)
    completed = 0
    for item in survey_rows:
        for version_code, label_col, zh_col in VERSION_COLUMNS:
            if version_code not in selected_versions:
                continue
            candidate_zh = item.get(zh_col, "")
            sample_id = f"{item.get('item_id', item.get('key', 'item'))}__{version_code}"
            try:
                result = graph.invoke(
                    {
                        "sample_id": sample_id,
                        "source_en": item.get("english", ""),
                        "candidate_zh": candidate_zh,
                        "version_code": version_code,
                        "version_label": item.get(label_col, version_code),
                    }
                )
                report = result["final_report"]
            except Exception as exc:
                report = {
                    "sample_id": sample_id,
                    "overall_score": "",
                    "dimension_scores": {},
                    "evidence_ids": [],
                    "route": "error",
                    "route_reason": "error",
                    "uncertainty": "",
                    "error": repr(exc),
                }
                result = {"final_report": report, "error": repr(exc)}
            flat_rows.append(
                flatten_report(
                    item=item,
                    version_code=version_code,
                    version_label=item.get(label_col, version_code),
                    candidate_zh=candidate_zh,
                    report=report,
                )
            )
            raw_rows.append(result)
            completed += 1
            print(f"[{completed}/{total}] {sample_id} score={report.get('overall_score')} route={report.get('route')}")

    write_csv(out_dir / "scores.csv", flat_rows)
    write_jsonl(out_dir / "raw_results.jsonl", raw_rows)
    manifest = {
        "run_name": run_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "survey_csv": str(args.survey_csv).replace("\\", "/"),
        "survey_rows": len(survey_rows),
        "evaluated_samples": len(flat_rows),
        "versions": sorted(selected_versions),
        "evaluation_mode": "single_candidate_vertical",
        "use_llm": not args.no_llm,
        "llm_client_active": llm_client_active,
        "use_retrieval": not args.no_rag,
        "embedding_backend": args.embedding_backend,
        "routing_threshold": args.routing_threshold,
        "low_score_threshold": args.low_score_threshold,
        "low_average_threshold": args.low_average_threshold,
        "preliminary_model": args.preliminary_model if not args.no_llm else None,
        "deep_audit_model": args.deep_audit_model if not args.no_llm else None,
        "outputs": {
            "scores_csv": str(out_dir / "scores.csv").replace("\\", "/"),
            "raw_results_jsonl": str(out_dir / "raw_results.jsonl").replace("\\", "/"),
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
