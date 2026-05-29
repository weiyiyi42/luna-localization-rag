"""Build a balanced 100-item survey sample with reduced ellipsis bias."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from build_survey_sample import (
    OUT,
    SOURCES,
    VERSION_ROOT,
    VERSIONS,
    change_score,
    en_col,
    flatten_for_csv,
    grouped_item_record,
    item_record,
    length_bucket,
    load_version_csv,
    localization_risk_score,
    norm,
    song_group_key,
    style_variance_score,
)


BALANCED_ALLOCATION = {
    "Song": 65,
    "UI": 25,
    "Achievements": 10,
}
TARGET_ELLIPSIS_ITEMS = 35
MAX_ELLIPSIS_PER_SOURCE = {
    "Song": 30,
    "UI": 5,
    "Achievements": 0,
}
MAX_PREFIX_ITEMS = 3
RANDOM_SEED = 20260514


def ellipsis_count(text: str) -> int:
    return text.count("...") + text.count("…") + text.count("â€¦")


def item_ellipsis_count(item: dict) -> int:
    count = ellipsis_count(item["english"])
    for translation in item["translations"]:
        count += ellipsis_count(translation["text"])
    return count


def key_prefix(key: str) -> str:
    parts = key.split("_")
    if len(parts) >= 2:
        return "_".join(parts[:2])
    return key


def enrich_item(item: dict) -> dict:
    item = dict(item)
    item["ellipsis_count"] = item_ellipsis_count(item)
    item["has_ellipsis"] = item["ellipsis_count"] > 0
    item["key_prefix"] = key_prefix(item["key"])
    ellipsis_penalty = min(item["ellipsis_count"], 10) * 0.45
    memory_penalty = 1.5 if item["key_prefix"].startswith(("THREAD_MEMORY", "MEMORY_")) else 0.0
    item["balanced_priority_score"] = round(
        item["sampling_priority_score"] - ellipsis_penalty - memory_penalty,
        3,
    )
    return item


def load_candidates() -> tuple[list[dict], dict[str, int]]:
    candidates: list[dict] = []
    counts: dict[str, int] = {}
    for source, filename, _target, should_group in SOURCES:
        loaded = [(code, label, load_version_csv(dirname, filename)) for code, label, dirname in VERSIONS]
        common = sorted(set.intersection(*(set(rows) for _, _, rows in loaded)))
        if should_group:
            grouped = defaultdict(list)
            for key in common:
                grouped[song_group_key(key)].append(key)
            source_candidates = [
                grouped_item_record(source, group_key, sorted(member_keys), loaded)
                for group_key, member_keys in grouped.items()
            ]
        else:
            source_candidates = [
                item_record(source, [(code, label, rows[key]) for code, label, rows in loaded], key)
                for key in common
            ]
        source_candidates = [enrich_item(item) for item in source_candidates]
        counts[source] = len(source_candidates)
        candidates.extend(source_candidates)
    return candidates, counts


def select_for_source(candidates: list[dict], source: str, target: int) -> list[dict]:
    source_items = [item for item in candidates if item["source_type"] == source and item["changed_across_versions"]]
    source_items.sort(
        key=lambda item: (
            -item["balanced_priority_score"],
            item["ellipsis_count"],
            -item["change_score"],
            item["item_id"],
        )
    )
    selected: list[dict] = []
    prefix_counts: Counter[str] = Counter()
    ellipsis_count_selected = 0
    max_source_ellipsis = MAX_ELLIPSIS_PER_SOURCE[source]

    for item in source_items:
        if len(selected) >= target:
            break
        prefix = item["key_prefix"]
        if prefix_counts[prefix] >= MAX_PREFIX_ITEMS:
            continue
        if item["has_ellipsis"] and ellipsis_count_selected >= max_source_ellipsis:
            continue
        selected.append(item)
        prefix_counts[prefix] += 1
        if item["has_ellipsis"]:
            ellipsis_count_selected += 1

    if len(selected) < target:
        selected_ids = {item["item_id"] for item in selected}
        for item in source_items:
            if len(selected) >= target:
                break
            if item["item_id"] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item["item_id"])
    return selected[:target]


def build_report(items: list[dict], candidate_counts: dict[str, int]) -> str:
    source_counts = Counter(item["source_type"] for item in items)
    ellipsis_by_source = Counter(item["source_type"] for item in items if item["has_ellipsis"])
    bucket_counts = Counter((item["source_type"], item["length_bucket"]) for item in items)
    prefix_counts = Counter(item["key_prefix"] for item in items)
    lines = [
        "# Balanced Survey Sampling Report",
        "",
        f"- Random seed: `{RANDOM_SEED}`",
        f"- Total selected items: `{len(items)}`",
        "- Sampling method: high-divergence purposive stratified sampling with ellipsis and key-prefix caps.",
        f"- Target ellipsis-heavy soft cap: `{TARGET_ELLIPSIS_ITEMS}`",
        "- Output files preserve the original `survey_items_master.*` files.",
        "",
        "## Source Allocation",
        "",
    ]
    for source in ["Song", "UI", "Achievements"]:
        lines.append(
            f"- {source}: {source_counts[source]} selected from {candidate_counts.get(source, 0)} candidates"
        )
    lines.extend(["", "## Ellipsis Counts", ""])
    total_ellipsis = sum(1 for item in items if item["has_ellipsis"])
    lines.append(f"- Total items containing ellipsis: {total_ellipsis}")
    lines.append(
        "- Note: the final count may exceed the soft cap when high-divergence candidates in the source allocation are predominantly ellipsis-heavy."
    )
    for source in ["Song", "UI", "Achievements"]:
        lines.append(f"- {source}: {ellipsis_by_source[source]}")
    lines.extend(["", "## Length Buckets", ""])
    for (source, bucket), count in sorted(bucket_counts.items()):
        lines.append(f"- {source} / {bucket}: {count}")
    lines.extend(["", "## Top Key Prefixes", ""])
    for prefix, count in prefix_counts.most_common(20):
        lines.append(f"- {prefix}: {count}")
    lines.extend(
        [
            "",
            "## Rationale",
            "",
            "The first survey sample over-represented ellipsis-heavy Song entries. This balanced sample keeps high-divergence and lore-sensitive items but reduces fragmentary memory-style text so that player-facing survey items are easier to judge.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates, candidate_counts = load_candidates()
    selected: list[dict] = []
    for source, target in BALANCED_ALLOCATION.items():
        selected.extend(select_for_source(candidates, source, target))

    selected.sort(key=lambda item: (item["source_type"], -item["balanced_priority_score"], item["item_id"]))
    rows = flatten_for_csv(selected)
    for row, item in zip(rows, selected):
        row["ellipsis_count"] = item["ellipsis_count"]
        row["has_ellipsis"] = item["has_ellipsis"]
        row["key_prefix"] = item["key_prefix"]
        row["balanced_priority_score"] = item["balanced_priority_score"]

    json_path = OUT / "survey_items_balanced.json"
    csv_path = OUT / "survey_items_balanced.csv"
    report_path = OUT / "balanced_sampling_report.md"
    json_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    report_path.write_text(build_report(selected, candidate_counts), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
