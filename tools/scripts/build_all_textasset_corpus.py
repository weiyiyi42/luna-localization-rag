"""Build aligned CSV files for all decrypted Silksong TextAssets.

The original extractor writes CSVs only for Song/UI/Achievements/Credits_List.
This script aligns every EN_* asset with its ZH_* counterpart across V1/V2/V3,
so regular NPC and area dialogue such as Belltown, Wanderers, Quests, Journal,
and region-specific files are available for sampling and RAG evidence.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION_ROOT = ROOT / "data" / "processed" / "silksong_versions"
OUT_DIR = ROOT / "data" / "processed" / "silksong_all_textassets"
VERSIONS = [
    ("V1", "Initial official version", "V1_existing_steam_content_revision_28324_manifest_unknown"),
    ("V2", "Public-beta official revision", "V2_public_beta_1.0.28954_official_revision_manifest_2538255789859855032"),
    ("V3", "Patch 4 Team Cart Fix version", "V3_patch4_team_cart_fix_revision_29315_manifest_3545882420322545098"),
]
EXCLUDED_GROUPS = {"Credits_List", "AutoSaveNames", "Error"}


def parse_entries(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    rows: dict[str, str] = {}
    for entry in root.findall(".//entry"):
        key = entry.attrib.get("name")
        if not key:
            continue
        rows[key] = clean_text(html.unescape("".join(entry.itertext())))
    return rows


def clean_text(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n")
    text = re.sub(r"<hpage>|<page(?:=[A-Z])?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def group_from_en_name(name: str) -> str:
    return name.removeprefix("EN_").removesuffix(".txt")


def discover_groups() -> list[str]:
    sets = []
    for _code, _label, dirname in VERSIONS:
        d = VERSION_ROOT / dirname / "textassets_decrypted"
        groups = {group_from_en_name(path.name) for path in d.glob("EN_*.txt")}
        sets.append(groups)
    return sorted(set.intersection(*sets))


def load_group(version_dir: str, group: str) -> tuple[dict[str, str], dict[str, str]]:
    d = VERSION_ROOT / version_dir / "textassets_decrypted"
    return parse_entries(d / f"EN_{group}.txt"), parse_entries(d / f"ZH_{group}.txt")


def length_bucket(text: str) -> str:
    n = len(text)
    if n <= 45:
        return "micro"
    if n <= 100:
        return "short"
    if n <= 220:
        return "medium"
    return "long"


def has_dialogue_markup(raw_text: str) -> bool:
    return "\n" in raw_text or bool(re.search(r"\b[A-Z][a-z]+[,:]", raw_text))


def row_for_group(group: str, key: str, loaded: list[tuple[str, str, dict[str, str], dict[str, str]]]) -> dict:
    first_en = loaded[0][2].get(key, "")
    row = {
        "item_id": f"{group}_{key}",
        "group": group,
        "key": key,
        "english": first_en,
        "length_bucket": length_bucket(first_en),
        "has_dialogue_markup": has_dialogue_markup(first_en),
    }
    zh_values = []
    for code, label, _en_entries, zh_entries in loaded:
        value = zh_entries.get(key, "")
        row[f"{code}_label"] = label
        row[f"{code}_zh"] = value
        zh_values.append(value)
    row["changed_across_versions"] = len(set(zh_values)) > 1
    row["ellipsis_count"] = sum(value.count("...") + value.count("…") for value in [first_en, *zh_values])
    row["has_ellipsis"] = row["ellipsis_count"] > 0
    return row


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--include-excluded", action="store_true")
    args = parser.parse_args()

    groups = discover_groups()
    if not args.include_excluded:
        groups = [group for group in groups if group not in EXCLUDED_GROUPS]

    all_rows: list[dict] = []
    group_counts = {}
    csv_dir = args.out_dir / "csv_by_group"
    for group in groups:
        loaded = []
        for code, label, dirname in VERSIONS:
            en_entries, zh_entries = load_group(dirname, group)
            loaded.append((code, label, en_entries, zh_entries))
        common_keys = sorted(set.intersection(*(set(en_entries) for _c, _l, en_entries, _z in loaded)))
        rows = [row_for_group(group, key, loaded) for key in common_keys]
        group_counts[group] = len(rows)
        all_rows.extend(rows)
        write_csv(csv_dir / f"{group}_V1_V2_V3.csv", rows)

    all_rows.sort(key=lambda row: (row["group"], row["key"]))
    write_csv(args.out_dir / "all_textassets_master.csv", all_rows)
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "versions": [{"code": code, "label": label, "directory": dirname} for code, label, dirname in VERSIONS],
        "excluded_groups": [] if args.include_excluded else sorted(EXCLUDED_GROUPS),
        "group_count": len(groups),
        "row_count": len(all_rows),
        "changed_rows": sum(1 for row in all_rows if row["changed_across_versions"]),
        "ellipsis_rows": sum(1 for row in all_rows if row["has_ellipsis"]),
        "dialogue_like_rows": sum(1 for row in all_rows if row["has_dialogue_markup"]),
        "group_counts": group_counts,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    source_counts = Counter(row["group"] for row in all_rows)
    report = [
        "# All TextAsset Corpus Report",
        "",
        f"- Groups exported: `{len(groups)}`",
        f"- Total aligned rows: `{len(all_rows)}`",
        f"- Changed across versions: `{manifest['changed_rows']}`",
        f"- Rows containing ellipsis: `{manifest['ellipsis_rows']}`",
        f"- Dialogue-like rows: `{manifest['dialogue_like_rows']}`",
        "",
        "## Largest Groups",
        "",
    ]
    for group, count in source_counts.most_common(20):
        report.append(f"- {group}: {count}")
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "The earlier CSV export covered only Song, UI, Achievements, and Credits_List. Regular NPC and regional dialogue is mostly stored in separate TextAssets such as Belltown, Wanderers, Quests, Journal, and region-specific files. These groups should be considered for survey sampling and RAG evidence.",
        ]
    )
    (args.out_dir / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
