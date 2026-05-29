"""Build Scheme C survey sample from all aligned TextAssets."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "processed" / "silksong_all_textassets" / "all_textassets_master.csv"
OUT = ROOT / "data" / "survey"
RANDOM_SEED = 20260514


SCHEME = {
    "dialogue": {
        "count": 45,
        "groups": {
            "Belltown",
            "Wanderers",
            "Bonebottom",
            "Caravan",
            "City",
            "Greymoor",
            "Wilds",
            "Enclave",
            "Forge",
            "Coral",
            "Dust",
            "Under",
            "Weave",
            "Shellwood",
            "Peak",
            "Crawl",
        },
    },
    "quest_interaction": {
        "count": 20,
        "groups": {"Quests", "Inspect", "Lore", "Fast_Travel", "Shop"},
    },
    "item_tool_ui": {
        "count": 20,
        "groups": {"Tools", "UI", "Prompts"},
    },
    "journal_lore": {
        "count": 10,
        "groups": {"Journal", "Lore"},
    },
    "achievement_map_title": {
        "count": 5,
        "groups": {"Map_Zones", "Titles"},
    },
}

MAX_ELLIPSIS_ITEMS = 30
MAX_SONG_ITEMS = 15
MAX_GROUP_ITEMS = 12
MAX_PREFIX_ITEMS = 3
MAX_MICRO_ITEMS = 15
MAX_LONG_ITEMS = 15


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def read_rows() -> list[dict]:
    with CORPUS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def key_prefix(key: str) -> str:
    parts = key.split("_")
    return "_".join(parts[:2]) if len(parts) >= 2 else key


def change_score(translations: list[str]) -> float:
    unique = len(set(translations))
    if unique <= 1:
        return 0.0
    lengths = [len(text) for text in translations]
    spread = max(lengths) - min(lengths)
    char_diversity = len(set("".join(translations)))
    return unique * 10 + min(spread, 120) / 10 + min(char_diversity, 160) / 40


def style_variance_score(translations: list[str]) -> float:
    punctuation = "，。！？；：、……—《》“”"
    classical = "兮吾汝尔焉矣者也其乃若于之乎"

    def features(text: str) -> tuple[int, int, int, int]:
        return (
            sum(text.count(ch) for ch in punctuation),
            sum(text.count(ch) for ch in classical),
            len(re.findall(r"[A-Za-z0-9]", text)),
            len(text),
        )

    values = [features(text) for text in translations]
    score = 0.0
    for idx in range(len(values[0])):
        column = [value[idx] for value in values]
        score += min(max(column) - min(column), 30) / 6
    return score


def lore_risk(row: dict) -> float:
    text = " ".join([row["english"], row["key"], row["group"]])
    score = 0.0
    if re.search(r"\b(?:Pharloom|Hornet|Citadel|Silk|Void|Weaver|Bell|Rosar|Lace|Shakra|Sherma|Garmond|Zaza|Nuu|Grand Mother|Soul Snare)\b", text, re.I):
        score += 4.0
    if row["group"] in {"Lore", "Journal", "Quests", "Tools", "Wanderers"}:
        score += 2.0
    if len(row["english"]) >= 80:
        score += 1.0
    return score


def visibility_score(row: dict, category: str) -> float:
    group = row["group"]
    score = {
        "dialogue": 5.0,
        "quest_interaction": 4.5,
        "item_tool_ui": 4.0,
        "journal_lore": 3.5,
        "achievement_map_title": 3.0,
    }[category]
    if row.get("has_dialogue_markup") == "True":
        score += 1.0
    if group in {"Deprecated", "Song"}:
        score -= 3.0
    return score


def ellipsis_count(row: dict) -> int:
    fields = [row["english"], row["V1_zh"], row["V2_zh"], row["V3_zh"]]
    return sum(text.count("...") + text.count("…") + text.count("â€¦") for text in fields)


def assign_category(row: dict) -> str | None:
    group = row["group"]
    for category, spec in SCHEME.items():
        if group in spec["groups"]:
            return category
    return None


def enrich(row: dict) -> dict:
    item = dict(row)
    category = assign_category(row)
    translations = [norm(row["V1_zh"]), norm(row["V2_zh"]), norm(row["V3_zh"])]
    item["category"] = category
    item["key_prefix"] = key_prefix(row["key"])
    item["change_score"] = round(change_score(translations), 3)
    item["style_variance_score"] = round(style_variance_score(translations), 3)
    item["lore_terminology_risk"] = round(lore_risk(row), 3)
    item["player_visibility"] = round(visibility_score(row, category or "dialogue"), 3) if category else 0.0
    item["ellipsis_count"] = ellipsis_count(row)
    item["has_ellipsis"] = item["ellipsis_count"] > 0
    item["changed_across_versions"] = len(set(translations)) > 1
    item["sampling_priority_score"] = round(
        0.40 * item["change_score"]
        + 0.20 * item["style_variance_score"]
        + 0.15 * item["lore_terminology_risk"]
        + 0.15 * item["player_visibility"],
        3,
    )
    item["scheme_c_score"] = round(
        item["sampling_priority_score"]
        - min(item["ellipsis_count"], 8) * 0.35
        - (1.5 if item["group"] == "Song" else 0.0),
        3,
    )
    return item


def can_select(item: dict, selected: list[dict], counters: dict[str, Counter]) -> bool:
    if item["source_type"] if "source_type" in item else False:
        pass
    if item["group"] == "Song" and counters["group"]["Song"] >= MAX_SONG_ITEMS:
        return False
    if counters["group"][item["group"]] >= MAX_GROUP_ITEMS:
        return False
    if counters["prefix"][item["key_prefix"]] >= MAX_PREFIX_ITEMS:
        return False
    if item["has_ellipsis"] and counters["flags"]["ellipsis"] >= MAX_ELLIPSIS_ITEMS:
        return False
    if item["length_bucket"] == "micro" and counters["length"]["micro"] >= MAX_MICRO_ITEMS:
        return False
    if item["length_bucket"] == "long" and counters["length"]["long"] >= MAX_LONG_ITEMS:
        return False
    return True


def add_item(item: dict, selected: list[dict], counters: dict[str, Counter]) -> None:
    selected.append(item)
    counters["group"][item["group"]] += 1
    counters["prefix"][item["key_prefix"]] += 1
    counters["length"][item["length_bucket"]] += 1
    counters["category"][item["category"]] += 1
    if item["has_ellipsis"]:
        counters["flags"]["ellipsis"] += 1


def select_items(candidates: list[dict]) -> list[dict]:
    selected: list[dict] = []
    counters = {
        "group": Counter(),
        "prefix": Counter(),
        "length": Counter(),
        "category": Counter(),
        "flags": Counter(),
    }
    used_ids: set[str] = set()

    for category, spec in SCHEME.items():
        pool = [
            item
            for item in candidates
            if item["category"] == category and item["changed_across_versions"]
        ]
        pool.sort(
            key=lambda item: (
                -item["scheme_c_score"],
                item["ellipsis_count"],
                -item["change_score"],
                item["item_id"],
            )
        )
        for item in pool:
            if counters["category"][category] >= spec["count"]:
                break
            if item["item_id"] in used_ids:
                continue
            if not can_select(item, selected, counters):
                continue
            add_item(item, selected, counters)
            used_ids.add(item["item_id"])

        if counters["category"][category] < spec["count"]:
            for item in pool:
                if counters["category"][category] >= spec["count"]:
                    break
                if item["item_id"] in used_ids:
                    continue
                if counters["group"][item["group"]] >= MAX_GROUP_ITEMS + 3:
                    continue
                add_item(item, selected, counters)
                used_ids.add(item["item_id"])

    return selected


def to_csv_row(item: dict) -> dict:
    return {
        "item_id": item["item_id"],
        "category": item["category"],
        "source_type": item["group"],
        "group": item["group"],
        "key": item["key"],
        "member_keys": item["key"],
        "english": item["english"],
        "length_bucket": item["length_bucket"],
        "changed_across_versions": item["changed_across_versions"],
        "change_score": item["change_score"],
        "style_variance_score": item["style_variance_score"],
        "localization_risk_score": item["lore_terminology_risk"],
        "player_visibility": item["player_visibility"],
        "sampling_priority_score": item["sampling_priority_score"],
        "scheme_c_score": item["scheme_c_score"],
        "V1_label": item["V1_label"],
        "V1_zh": item["V1_zh"],
        "V2_label": item["V2_label"],
        "V2_zh": item["V2_zh"],
        "V3_label": item["V3_label"],
        "V3_zh": item["V3_zh"],
        "ellipsis_count": item["ellipsis_count"],
        "has_ellipsis": item["has_ellipsis"],
        "key_prefix": item["key_prefix"],
    }


def write_outputs(selected: list[dict], candidates: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    selected.sort(key=lambda item: (item["category"], -item["scheme_c_score"], item["item_id"]))
    rows = [to_csv_row(item) for item in selected]
    suffix = "scheme_c_no_general_achievements"
    csv_path = OUT / f"survey_items_{suffix}.csv"
    json_path = OUT / f"survey_items_{suffix}.json"
    report_path = OUT / f"{suffix}_sampling_report.md"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    category_counts = Counter(item["category"] for item in selected)
    group_counts = Counter(item["group"] for item in selected)
    length_counts = Counter(item["length_bucket"] for item in selected)
    report = [
        "# Scheme C Survey Sampling Report",
        "",
        f"- Random seed: `{RANDOM_SEED}`",
        f"- Candidate corpus: `{CORPUS}`",
        f"- Total candidates considered: `{len(candidates)}`",
        f"- Total selected: `{len(selected)}`",
        "- Sampling weights: 40% version difference, 20% style variance, 15% lore/terminology risk, 15% player visibility, with penalties/caps for ellipsis and overrepresented groups.",
        "",
        "## Category Allocation",
        "",
    ]
    for category, spec in SCHEME.items():
        report.append(f"- {category}: {category_counts[category]} / target {spec['count']}")
    report.extend(["", "## Quality Controls", ""])
    report.append(f"- Items with ellipsis: {sum(1 for item in selected if item['has_ellipsis'])}")
    report.append(f"- Micro items: {length_counts['micro']}")
    report.append(f"- Long items: {length_counts['long']}")
    report.extend(["", "## Source Groups", ""])
    for group, count in group_counts.most_common():
        report.append(f"- {group}: {count}")
    report.extend(["", "## Length Buckets", ""])
    for bucket, count in sorted(length_counts.items()):
        report.append(f"- {bucket}: {count}")
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")


def main() -> None:
    raw_rows = read_rows()
    candidates = [enrich(row) for row in raw_rows]
    candidates = [
        item
        for item in candidates
        if item["category"]
        and item["changed_across_versions"]
        and norm(item["english"])
        and norm(item["V1_zh"])
        and norm(item["V2_zh"])
        and norm(item["V3_zh"])
    ]
    selected = select_items(candidates)
    if len(selected) != 100:
        raise SystemExit(f"Expected 100 selected items, got {len(selected)}")
    write_outputs(selected, candidates)


if __name__ == "__main__":
    main()
