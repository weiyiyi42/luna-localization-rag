"""Fetch Silksong-related MediaWiki pages into a local, reproducible snapshot.

The thesis design calls for a controlled local knowledge base rather than
live web search during evaluation. This script creates that source snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


DEFAULT_API = "https://hollowknight.fandom.com/api.php"
DEFAULT_TERMS = [
    "Silksong",
    '"Hollow Knight: Silksong"',
    "Hunter's Journal Silksong",
    "Silksong character",
    "Silksong location",
    "Silksong item",
    "Silksong tool",
    "Silksong boss",
    "Silksong enemy",
    "Silksong quest",
    "Silksong lore",
]


def slugify(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title.strip()).strip("_")
    return slug.lower() or "page"


def api_get(api_url: str, params: dict[str, Any], delay: float) -> dict[str, Any]:
    headers = {
        "User-Agent": "hk-research-luna/0.1 (local thesis knowledge-base snapshot)"
    }
    response = requests.get(api_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    if delay:
        time.sleep(delay)
    return response.json()


def search_titles(api_url: str, terms: list[str], limit_per_term: int, delay: float) -> list[str]:
    seen: set[str] = set()
    titles: list[str] = []
    for term in terms:
        payload = api_get(
            api_url,
            {
                "action": "query",
                "list": "search",
                "srsearch": term,
                "srnamespace": 0,
                "srlimit": limit_per_term,
                "format": "json",
            },
            delay,
        )
        for item in payload.get("query", {}).get("search", []):
            title = item.get("title", "").strip()
            if title and title not in seen:
                seen.add(title)
                titles.append(title)
    return titles


def fetch_pages(api_url: str, titles: list[str], delay: float) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for title in titles:
        payload = api_get(
            api_url,
            {
                "action": "parse",
                "page": title,
                "prop": "text|categories|displaytitle",
                "redirects": 1,
                "format": "json",
            },
            delay,
        )
        parsed = payload.get("parse", {})
        html = parsed.get("text", {}).get("*", "")
        text = html_to_text(html)
        if not title or not text:
            continue
        categories = [
            c.get("*", "")
            for c in parsed.get("categories", [])
            if not c.get("hidden") and c.get("*")
        ]
        page_title = parsed.get("title", title).strip()
        pages.append(
            {
                "source_type": "wiki",
                "page_id": parsed.get("pageid"),
                "title": page_title,
                "url": f"https://hollowknight.fandom.com/wiki/{quote(page_title.replace(' ', '_'))}",
                "categories": categories,
                "text": text,
            }
        )
    return pages


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select(
        "script, style, sup.reference, table, aside, figure, .toc, .mw-editsection, "
        ".portable-infobox, .navbox, .gallery, .wds-tab__content, .references"
    ):
        node.decompose()
    pieces: list[str] = []
    content = soup.select_one(".mw-parser-output") or soup
    for node in content.find_all(["h2", "h3", "p", "ul", "ol"], recursive=False):
        if node.name in {"ul", "ol"}:
            candidates = node.find_all("li", recursive=False)
        else:
            candidates = [node]
        for candidate in candidates:
            text = candidate.get_text(" ", strip=True)
            if not text:
                continue
            if text.lower() in {"navigation", "gallery", "references"}:
                continue
            pieces.append(text)
    return normalise_text("\n".join(pieces))


def normalise_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def keep_page(page: dict[str, Any], require_silksong: bool, min_chars: int) -> bool:
    text = f"{page.get('title', '')}\n{page.get('text', '')}"
    if len(page.get("text", "")) < min_chars:
        return False
    if not require_silksong:
        return True
    return bool(re.search(r"Silksong|Pharloom|Hornet|Hunter's Journal", text, re.I))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--out-dir", default="data/raw/silksong_wiki")
    parser.add_argument("--term", action="append", dest="terms", help="Search term. Can be repeated.")
    parser.add_argument("--limit-per-term", type=int, default=30)
    parser.add_argument("--min-chars", type=int, default=200)
    parser.add_argument("--no-require-silksong", action="store_true")
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    terms = args.terms or DEFAULT_TERMS
    fetched_at = datetime.now(timezone.utc).isoformat()

    titles = search_titles(args.api_url, terms, args.limit_per_term, args.delay)
    pages = fetch_pages(args.api_url, titles, args.delay)
    pages = [
        {**page, "evidence_id": f"wiki:{slugify(page['title'])}"}
        for page in pages
        if keep_page(page, not args.no_require_silksong, args.min_chars)
    ]
    pages.sort(key=lambda row: row["title"].lower())

    snapshot_path = out_dir / "pages.jsonl"
    write_jsonl(snapshot_path, pages)
    manifest = {
        "source": args.api_url,
        "fetched_at": fetched_at,
        "search_terms": terms,
        "limit_per_term": args.limit_per_term,
        "page_count": len(pages),
        "snapshot": str(snapshot_path).replace("\\", "/"),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
