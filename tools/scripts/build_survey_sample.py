import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION_ROOT = ROOT / "data" / "processed" / "silksong_versions"
OUT = ROOT / "data" / "survey"

VERSIONS = [
    ("V1", "Initial official version", "V1_existing_steam_content_revision_28324_manifest_unknown"),
    ("V2", "Public-beta official revision", "V2_public_beta_1.0.28954_official_revision_manifest_2538255789859855032"),
    ("V3", "Patch 4 Team Cart Fix version", "V3_patch4_team_cart_fix_revision_29315_manifest_3545882420322545098"),
]

SOURCES = [
    ("Song", "Song_EN_ZH.csv", 80, True),
    ("UI", "UI_EN_ZH.csv", 15, False),
    ("Achievements", "Achievements_EN_ZH.csv", 5, False),
]

RANDOM_SEED = 20260512


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def zh_col(row: dict, source: str) -> str:
    candidates = [c for c in row if c.startswith("ZH_") and not c.startswith("ZH_TW")]
    if candidates:
        return candidates[0]
    expected = f"ZH_{source}"
    return expected if expected in row else "ZH_Song"


def en_col(row: dict, source: str) -> str:
    expected = f"EN_{source}"
    if expected in row:
        return expected
    candidates = [c for c in row if c.startswith("EN_")]
    return candidates[0] if candidates else "EN_Song"


def load_version_csv(version_dir: str, filename: str) -> dict:
    path = VERSION_ROOT / version_dir / "csv" / filename
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {row["key"]: row for row in csv.DictReader(f)}


def length_bucket(text: str) -> str:
    n = len(text)
    if n <= 45:
        return "micro"
    if n <= 100:
        return "short"
    if n <= 220:
        return "medium"
    return "long"


def song_group_key(key: str) -> str:
    return re.sub(r"_(?:\d{1,3}|[A-Z]\d{1,3})$", "", key)


def change_score(translations: list[str]) -> float:
    unique = len(set(translations))
    if unique <= 1:
        return 0.0
    lengths = [len(t) for t in translations]
    spread = max(lengths) - min(lengths)
    tokenish = len(set("".join(translations)))
    return unique * 10 + min(spread, 80) / 8 + min(tokenish, 120) / 30


def style_variance_score(translations: list[str]) -> float:
    archaic_markers = "兮吾汝尔焉矣者也其乃若于之乎"
    punctuation = "，。！？；：、……—"

    def features(text: str) -> tuple[int, int, int, int]:
        return (
            sum(text.count(ch) for ch in archaic_markers),
            sum(text.count(ch) for ch in punctuation),
            len(re.findall(r"[A-Za-z0-9]", text)),
            len(text),
        )

    values = [features(text) for text in translations]
    score = 0.0
    for idx in range(len(values[0])):
        column = [value[idx] for value in values]
        score += min(max(column) - min(column), 20) / 4
    return score


def localization_risk_score(source: str, key: str, english: str, translations: list[str]) -> float:
    score = 0.0
    if source == "Song":
        score += 8.0
    if source == "UI":
        score += 3.0
    if len(english) >= 80:
        score += 4.0
    if re.search(r"[A-Z][A-Z_]{2,}", key):
        score += 2.0
    if any("..." in text or "…" in text for text in translations):
        score += 1.5
    return score


def item_record(source: str, rows_by_version: list[tuple[str, str, dict]], key: str) -> dict:
    first_row = rows_by_version[0][2]
    source_text = norm(first_row[en_col(first_row, source)])
    translations = []
    for code, label, row in rows_by_version:
        translations.append(
            {
                "version": code,
                "version_label": label,
                "text": norm(row[zh_col(row, source)]),
            }
        )
    zh_texts = [t["text"] for t in translations]
    base_change_score = change_score(zh_texts)
    style_score = style_variance_score(zh_texts)
    risk_score = localization_risk_score(source, key, source_text, zh_texts)
    return {
        "item_id": f"{source}_{key}",
        "source_type": source,
        "key": key,
        "english": source_text,
        "length_bucket": length_bucket(source_text),
        "changed_across_versions": len(set(zh_texts)) > 1,
        "change_score": round(base_change_score, 3),
        "style_variance_score": round(style_score, 3),
        "localization_risk_score": round(risk_score, 3),
        "sampling_priority_score": round(base_change_score * 0.65 + style_score * 0.2 + risk_score * 0.15, 3),
        "translations": translations,
    }


def grouped_item_record(source: str, group_key: str, member_keys: list[str], loaded: list[tuple[str, str, dict]]) -> dict:
    translations = []
    english_lines = []
    for code, label, rows in loaded:
        zh_lines = []
        for key in member_keys:
            row = rows[key]
            if code == loaded[0][0]:
                english_lines.append(norm(row[en_col(row, source)]))
            zh_lines.append(norm(row[zh_col(row, source)]))
        translations.append(
            {
                "version": code,
                "version_label": label,
                "text": "\n".join(line for line in zh_lines if line),
            }
        )
    source_text = "\n".join(line for line in english_lines if line)
    zh_texts = [t["text"] for t in translations]
    base_change_score = change_score(zh_texts)
    style_score = style_variance_score(zh_texts)
    risk_score = localization_risk_score(source, group_key, source_text, zh_texts) + min(len(member_keys), 8)
    return {
        "item_id": f"{source}_{group_key}",
        "source_type": source,
        "key": group_key,
        "member_keys": "|".join(member_keys),
        "english": source_text,
        "length_bucket": length_bucket(source_text),
        "changed_across_versions": len(set(zh_texts)) > 1,
        "change_score": round(base_change_score, 3),
        "style_variance_score": round(style_score, 3),
        "localization_risk_score": round(risk_score, 3),
        "sampling_priority_score": round(base_change_score * 0.65 + style_score * 0.2 + risk_score * 0.15, 3),
        "translations": translations,
    }


def stratified_select(items: list[dict], n: int) -> list[dict]:
    changed = [x for x in items if x["changed_across_versions"]]
    unchanged = [x for x in items if not x["changed_across_versions"]]
    changed.sort(key=lambda x: (-x["sampling_priority_score"], -x["change_score"], x["item_id"]))
    unchanged.sort(key=lambda x: (-len(x["english"]), x["item_id"]))

    target_changed = min(len(changed), math.ceil(n * 0.85))
    seed_pool = changed[: max(target_changed * 3, target_changed)]

    buckets = defaultdict(list)
    for item in seed_pool:
        buckets[item["length_bucket"]].append(item)

    selected = []
    bucket_order = ["micro", "short", "medium", "long"]
    while len(selected) < target_changed and any(buckets.values()):
        for bucket in bucket_order:
            if buckets[bucket] and len(selected) < target_changed:
                selected.append(buckets[bucket].pop(0))

    selected_ids = {x["item_id"] for x in selected}
    for item in changed + unchanged:
        if len(selected) >= n:
            break
        if item["item_id"] not in selected_ids:
            selected.append(item)
            selected_ids.add(item["item_id"])

    return selected[:n]


def flatten_for_csv(items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        base = {
            "item_id": item["item_id"],
            "source_type": item["source_type"],
            "key": item["key"],
            "member_keys": item.get("member_keys", item["key"]),
            "english": item["english"],
            "length_bucket": item["length_bucket"],
            "changed_across_versions": item["changed_across_versions"],
            "change_score": item["change_score"],
            "style_variance_score": item["style_variance_score"],
            "localization_risk_score": item["localization_risk_score"],
            "sampling_priority_score": item["sampling_priority_score"],
        }
        for trans in item["translations"]:
            base[f"{trans['version']}_label"] = trans["version_label"]
            base[f"{trans['version']}_zh"] = trans["text"]
        rows.append(base)
    return rows


def main() -> None:
    random.seed(RANDOM_SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    all_selected = []
    counts = {}
    candidates_count = {}
    for source, filename, target, should_group in SOURCES:
        loaded = [(code, label, load_version_csv(dirname, filename)) for code, label, dirname in VERSIONS]
        common = sorted(set.intersection(*(set(rows) for _, _, rows in loaded)))
        if should_group:
            grouped = defaultdict(list)
            for key in common:
                grouped[song_group_key(key)].append(key)
            candidates = [
                grouped_item_record(source, group_key, sorted(member_keys), loaded)
                for group_key, member_keys in grouped.items()
            ]
        else:
            candidates = [item_record(source, [(code, label, rows[key]) for code, label, rows in loaded], key) for key in common]
        candidates_count[source] = len(candidates)
        selected = stratified_select(candidates, target)
        counts[source] = len(selected)
        all_selected.extend(selected)

    all_selected.sort(key=lambda x: (x["source_type"], -x["change_score"], x["item_id"]))

    json_path = OUT / "survey_items_master.json"
    csv_path = OUT / "survey_items_master.csv"
    report_path = OUT / "sampling_report.md"

    json_path.write_text(json.dumps(all_selected, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = flatten_for_csv(all_selected)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    changed_count = sum(1 for x in all_selected if x["changed_across_versions"])
    bucket_counts = defaultdict(int)
    for item in all_selected:
        bucket_counts[(item["source_type"], item["length_bucket"])] += 1

    report = [
        "# Survey Sampling Report",
        "",
        f"- Random seed: `{RANDOM_SEED}`",
        f"- Total selected items: `{len(all_selected)}`",
        f"- Changed across versions: `{changed_count}`",
        "- Target allocation: Song 80, UI 15, Achievements 5.",
        "- Credits were excluded because credit text is less relevant to player-facing narrative localization quality.",
        "- Sampling method: high-divergence purposive stratified sampling.",
        "- Priority score: 65% cross-version textual divergence, 20% style variance, and 15% localization-risk weighting.",
        "",
        "## Candidate Counts",
        "",
    ]
    for source in [x[0] for x in SOURCES]:
        report.append(f"- {source}: {candidates_count[source]} candidates, {counts[source]} selected")
    report.extend(["", "## Length Buckets", ""])
    for (source, bucket), count in sorted(bucket_counts.items()):
        report.append(f"- {source} / {bucket}: {count}")
    report.extend(
        [
            "",
            "## Survey Recommendation",
            "",
            "Each participant should rate 20 randomly selected items. For each item, the three Chinese versions are anonymized and shuffled.",
            "With 30-50 participants, this design yields about 6-10 ratings per master item on average, while keeping individual workload manageable.",
            "",
            "## Internet Controversy Notes",
            "",
            "Chinese community controversy can be used to justify the sampling dimensions, especially style mismatch, readability, terminology, and lore consistency.",
            "However, community complaints should not be used as the direct sampling frame unless they are collected through a documented and reproducible protocol.",
            "The present sample therefore uses local corpus divergence as the primary sampling criterion and treats public controversy as contextual justification.",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
