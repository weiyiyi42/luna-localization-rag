"""Analyze a completed LUNA survey evaluation run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_RUN_DIR = Path("data/processed/luna_runs/survey_eval/deepseek_full")


def markdown_table(df: pd.DataFrame) -> str:
    flat = df.copy()
    flat.columns = [
        " ".join(str(part) for part in col if str(part))
        if isinstance(col, tuple)
        else str(col)
        for col in flat.columns
    ]
    flat = flat.reset_index()
    columns = [str(col) for col in flat.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in flat.iterrows():
        values = [str(row[col]) for col in flat.columns]
        lines.append("| " + " | ".join(value.replace("\n", " ") for value in values) + " |")
    return "\n".join(lines)


def winner_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    pivot = df.pivot_table(index="item_id", columns="version_code", values="overall_score", aggfunc="first")
    strict_winners: list[str] = []
    tie_count = 0
    winner_rows = []
    for item_id, row in pivot.iterrows():
        max_score = row.max()
        winners = [version for version, value in row.items() if value == max_score]
        if len(winners) == 1:
            strict_winners.append(winners[0])
        else:
            tie_count += 1
        winner_rows.append(
            {
                "item_id": item_id,
                "V1": row.get("V1"),
                "V2": row.get("V2"),
                "V3": row.get("V3"),
                "top_score": max_score,
                "winners": ",".join(winners),
            }
        )
    summary = {
        "strict_winner_counts": pd.Series(strict_winners).value_counts().to_dict(),
        "tie_count": tie_count,
    }
    return pd.DataFrame(winner_rows), summary


def pairwise_summary(winners: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for left, right in [("V3", "V1"), ("V3", "V2"), ("V2", "V1")]:
        diff = winners[left] - winners[right]
        rows.append(
            {
                "comparison": f"{left}-{right}",
                "mean_diff": round(diff.mean(), 3),
                f"{left}_wins": int((diff > 0).sum()),
                f"{right}_wins": int((diff < 0).sum()),
                "ties": int((diff == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def deep_audit_rate_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for version_code, group in df.groupby("version_code"):
        total = len(group)
        deep_audit_count = int((group["route"] == "deep_audit").sum())
        rows.append(
            {
                "version_code": version_code,
                "samples": total,
                "deep_audit_count": deep_audit_count,
                "deep_audit_rate": round(deep_audit_count / total, 3) if total else 0.0,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()

    scores_path = args.run_dir / "scores.csv"
    df = pd.read_csv(scores_path)
    for col in [
        "overall_score",
        "meaning_score",
        "lore_score",
        "style_score",
        "deep_audit_score",
        "uncertainty",
        "change_score",
        "style_variance_score",
        "localization_risk_score",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    version_summary = (
        df.groupby("version_code")[["overall_score", "meaning_score", "lore_score", "style_score", "uncertainty"]]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(3)
    )
    dimension_means = df.groupby("version_code")[["meaning_score", "lore_score", "style_score"]].mean().round(3)
    winners, winner_stats = winner_summary(df)
    pairwise = pairwise_summary(winners)
    source_summary = (
        df.groupby(["source_type", "version_code"])["overall_score"].agg(["count", "mean", "median"]).round(3)
    )
    length_summary = (
        df.groupby(["length_bucket", "version_code"])["overall_score"].agg(["count", "mean", "median"]).round(3)
    )
    route_summary = pd.crosstab(df["version_code"], df["route"])
    deep_audit_rates = deep_audit_rate_summary(df)
    route_reason_summary = (
        pd.crosstab(df["version_code"], df["route_reason"])
        if "route_reason" in df.columns
        else pd.DataFrame()
    )

    winners_path = args.run_dir / "winner_by_item.csv"
    winners.to_csv(winners_path, index=False, encoding="utf-8-sig")

    spread = winners.copy()
    spread["range"] = spread[["V1", "V2", "V3"]].max(axis=1) - spread[["V1", "V2", "V3"]].min(axis=1)
    largest_spread = spread.sort_values("range", ascending=False).head(15)
    largest_spread.to_csv(args.run_dir / "largest_score_spread.csv", index=False, encoding="utf-8-sig")

    report_lines = [
        "# LUNA Survey Evaluation Analysis",
        "",
        f"Run directory: `{args.run_dir}`",
        f"Rows: {len(df)}",
        f"Items: {df['item_id'].nunique()}",
        "",
        "## Version Summary",
        "",
        markdown_table(version_summary),
        "",
        "## Dimension Means",
        "",
        markdown_table(dimension_means),
        "",
        "## Strict Winners",
        "",
        json.dumps(winner_stats, ensure_ascii=False, indent=2),
        "",
        "## Pairwise Version Comparisons",
        "",
        markdown_table(pairwise.set_index("comparison")),
        "",
        "## Route Summary",
        "",
        markdown_table(route_summary),
        "",
        "## Deep Audit Rate By Version",
        "",
        markdown_table(deep_audit_rates.set_index("version_code")),
        "",
        "## Route Reason Summary",
        "",
        markdown_table(route_reason_summary) if not route_reason_summary.empty else "Route reasons were not logged for this run.",
        "",
        "## Source Type Summary",
        "",
        markdown_table(source_summary),
        "",
        "## Length Bucket Summary",
        "",
        markdown_table(length_summary),
        "",
        "## Largest Version Score Spread",
        "",
        markdown_table(largest_spread.set_index("item_id")),
        "",
        "## Notes",
        "",
        "- `deep_audit` count indicates how often adaptive routing selected the expensive path.",
        "- A high number of ties suggests the current scoring prompt/model may be conservative or coarse-grained.",
        "- The current run uses the embedding backend recorded in the run manifest; interpret retrieval quality accordingly.",
    ]
    (args.run_dir / "analysis_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.run_dir / "analysis_report.md"), "winners": str(winners_path)}, indent=2))


if __name__ == "__main__":
    main()
