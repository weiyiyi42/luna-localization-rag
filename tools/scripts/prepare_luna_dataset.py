"""Prepare a curated LUNA evidence dataset before vectorisation.

This script turns raw wiki pages and extracted Silksong CSV files into a
deduplicated, source-tiered knowledge dataset for the thesis RAG pipeline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_WIKI_JSONL = Path("data/raw/silksong_wiki/pages.jsonl")
DEFAULT_VERSIONS_DIR = Path("data/processed/silksong_versions")
DEFAULT_OUT_DIR = Path("data/processed/luna_knowledge_base")
CSV_TEXT_COLUMNS = {
    "Song_EN_ZH.csv": ("Song", "EN_Song", "ZH_Song"),
    "UI_EN_ZH.csv": ("UI", "EN_UI", "ZH_UI"),
    "Achievements_EN_ZH.csv": ("Achievements", "EN_Achievements", "ZH_Achievements"),
    "Credits_List_EN_ZH.csv": ("Credits_List", "EN_Credits_List", "ZH_Credits_List"),
}
NOISY_SECTION_HEADINGS = {
    "behavior and tactics",
    "achievements",
    "trivia",
    "dream nail dialogue",
    "references",
}
TERM_STOPWORDS = {
    "A",
    "An",
    "All",
    "And",
    "Are",
    "As",
    "At",
    "Back",
    "Be",
    "Can",
    "Do",
    "For",
    "From",
    "Go",
    "Has",
    "Have",
    "How",
    "Hollow",
    "Knight",
    "Silksong",
    "In",
    "Into",
    "Is",
    "It",
    "Let",
    "May",
    "Must",
    "No",
    "Not",
    "Now",
    "Of",
    "On",
    "Only",
    "Or",
    "Our",
    "Out",
    "She",
    "Take",
    "That",
    "The",
    "This",
    "To",
    "Up",
    "Use",
    "Was",
    "What",
    "When",
    "Where",
    "Who",
    "Why",
    "Will",
    "With",
    "You",
    "Your",
    "After",
    "Before",
    "While",
    "Using",
    "There",
    "They",
    "These",
    "Health",
    "Silk",
    "Tools",
    "Abilities",
    "Trivia",
    "References",
    "Act",
}


def read_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text.strip()).strip("_")
    return slug.lower() or "item"


def stable_hash(text: str, length: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80:
        return False
    if line.endswith("."):
        return False
    return bool(re.match(r"^[A-Z][A-Za-z0-9 ':/&()-]+$", line))


def split_wiki_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("overview", [])]
    current = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if is_heading(line):
            sections.append((slugify(line), []))
            current = len(sections) - 1
            continue
        sections[current][1].append(line)
    return [(heading, clean_text(" ".join(lines))) for heading, lines in sections if clean_text(" ".join(lines))]


def wiki_evidence(path: Path) -> tuple[list[dict], dict[str, int]]:
    rows: list[dict] = []
    stats = Counter()
    for page in read_jsonl(path):
        title = page.get("title", "")
        categories = page.get("categories", [])
        is_silksong = "Silksong" in f"{title} {' '.join(categories)} {page.get('text', '')}"
        if not is_silksong:
            stats["wiki_pages_dropped_not_silksong"] += 1
            continue
        base_id = page.get("evidence_id") or f"wiki:{slugify(title)}"
        for section, text in split_wiki_sections(page.get("text", "")):
            if section in {slugify(s) for s in NOISY_SECTION_HEADINGS}:
                stats["wiki_sections_dropped_noisy"] += 1
                continue
            if len(text) < 80:
                stats["wiki_sections_dropped_short"] += 1
                continue
            tier = "wiki_lore"
            if "tweets" in title.lower():
                tier = "community_or_notes"
            rows.append(
                {
                    "evidence_id": f"{base_id}:section:{section}",
                    "source_type": tier,
                    "trust_level": 2 if tier == "wiki_lore" else 1,
                    "title": title,
                    "section": section,
                    "url": page.get("url", ""),
                    "categories": categories,
                    "text": f"{title}\n{section.replace('_', ' ').title()}\n\n{text}",
                }
            )
    return rows, dict(stats)


def version_label(version_name: str) -> str:
    if version_name.startswith("V1_"):
        return "V1"
    if version_name.startswith("V2_"):
        return "V2"
    if version_name.startswith("V3_"):
        return "V3"
    return version_name.split("_", 1)[0]


def game_evidence(versions_dir: Path) -> tuple[list[dict], dict[str, int]]:
    grouped: dict[tuple[str, str, str], dict] = {}
    raw_count = 0
    for version_dir in sorted(p for p in versions_dir.iterdir() if p.is_dir()):
        csv_dir = version_dir / "csv"
        if not csv_dir.exists():
            continue
        for csv_name, (corpus, en_col, zh_col) in CSV_TEXT_COLUMNS.items():
            path = csv_dir / csv_name
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    key = clean_text(row.get("key") or "")
                    english = clean_text(row.get(en_col) or "")
                    chinese = clean_text(row.get(zh_col) or "")
                    if not key or not english:
                        continue
                    raw_count += 1
                    group_key = (corpus, key, english)
                    record = grouped.setdefault(
                        group_key,
                        {
                            "corpus": corpus,
                            "key": key,
                            "english": english,
                            "versions": [],
                            "translations": {},
                        },
                    )
                    label = version_label(version_dir.name)
                    record["versions"].append(version_dir.name)
                    if chinese:
                        record["translations"][label] = chinese

    rows: list[dict] = []
    for (corpus, key, english), record in sorted(grouped.items()):
        suffix = stable_hash(f"{corpus}:{key}:{english}")
        rows.append(
            {
                "evidence_id": f"official_game_text:{corpus}:{key}:{suffix}",
                "source_type": "official_game_text",
                "trust_level": 3,
                "corpus": corpus,
                "key": key,
                "versions": record["versions"],
                "translations": record["translations"],
                "text": english,
            }
        )
    stats = {
        "game_rows_raw": raw_count,
        "game_rows_after_dedup": len(rows),
        "game_rows_deduplicated": raw_count - len(rows),
    }
    return rows, stats


def extract_terms(evidence_rows: list[dict]) -> list[dict]:
    term_sources: dict[str, dict] = {}
    pattern = re.compile(r"\b(?:[A-Z][a-z]+(?:['-][A-Z]?[a-z]+)?)(?:\s+[A-Z][a-z]+(?:['-][A-Z]?[a-z]+)?)*\b")
    for row in evidence_rows:
        text = row.get("text", "")
        for match in pattern.finditer(text):
            term = match.group(0).strip()
            if len(term) < 3 or term in TERM_STOPWORDS:
                continue
            if len(term.split()) == 1 and term not in text[:120] and row.get("source_type") != "wiki_lore":
                continue
            if len(term.split()) > 5:
                continue
            if term.lower() in {"overview", "section"}:
                continue
            entry = term_sources.setdefault(
                term,
                {
                    "term_id": f"term:{slugify(term)}",
                    "term": term,
                    "source_types": set(),
                    "evidence_ids": [],
                    "frequency": 0,
                },
            )
            entry["source_types"].add(row.get("source_type", "unknown"))
            if len(entry["evidence_ids"]) < 8 and row["evidence_id"] not in entry["evidence_ids"]:
                entry["evidence_ids"].append(row["evidence_id"])
            entry["frequency"] += 1
    terms = []
    for entry in term_sources.values():
        if entry["frequency"] < 2 and "official_game_text" not in entry["source_types"]:
            continue
        entry["source_types"] = sorted(entry["source_types"])
        terms.append(entry)
    terms.sort(key=lambda item: (-item["frequency"], item["term"].lower()))
    return terms


def write_report(path: Path, evidence_rows: list[dict], terms: list[dict], stats: dict[str, int]) -> None:
    counts = Counter(row["source_type"] for row in evidence_rows)
    trust_counts = Counter(str(row["trust_level"]) for row in evidence_rows)
    short_rows = [row for row in evidence_rows if len(row.get("text", "")) < 20]
    lines = [
        "# LUNA Knowledge Base Processing Report",
        "",
        f"Built at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Evidence Counts",
        "",
    ]
    for source_type, count in sorted(counts.items()):
        lines.append(f"- {source_type}: {count}")
    lines.extend(
        [
            f"- total: {len(evidence_rows)}",
            "",
            "## Trust Levels",
            "",
        ]
    )
    for trust_level, count in sorted(trust_counts.items()):
        lines.append(f"- {trust_level}: {count}")
    lines.extend(["", "## Processing Stats", ""])
    for key, value in sorted(stats.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Terminology",
            "",
            f"- extracted_terms: {len(terms)}",
            "",
            "## Quality Checks",
            "",
            f"- short_evidence_rows_under_20_chars: {len(short_rows)}",
            "",
            "## Top Terms",
            "",
        ]
    )
    for term in terms[:30]:
        lines.append(f"- {term['term']} ({term['frequency']})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-jsonl", type=Path, default=DEFAULT_WIKI_JSONL)
    parser.add_argument("--versions-dir", type=Path, default=DEFAULT_VERSIONS_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    wiki_rows, wiki_stats = wiki_evidence(args.wiki_jsonl)
    game_rows, game_stats = game_evidence(args.versions_dir)
    evidence_rows = sorted(
        wiki_rows + game_rows,
        key=lambda row: (row["source_type"], row.get("corpus", ""), row.get("title", ""), row["evidence_id"]),
    )
    terms = extract_terms(evidence_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    evidence_count = write_jsonl(args.out_dir / "evidence.jsonl", evidence_rows)
    term_count = write_jsonl(args.out_dir / "terminology.jsonl", terms)
    stats = {**wiki_stats, **game_stats, "evidence_rows": evidence_count, "terminology_rows": term_count}
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "wiki_jsonl": str(args.wiki_jsonl).replace("\\", "/"),
            "versions_dir": str(args.versions_dir).replace("\\", "/"),
        },
        "outputs": {
            "evidence": str(args.out_dir / "evidence.jsonl").replace("\\", "/"),
            "terminology": str(args.out_dir / "terminology.jsonl").replace("\\", "/"),
            "report": str(args.out_dir / "processing_report.md").replace("\\", "/"),
        },
        "stats": stats,
    }
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(args.out_dir / "processing_report.md", evidence_rows, terms, stats)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
