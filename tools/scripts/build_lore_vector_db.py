"""Build LUNA's local lore vector database with ChromaDB.

Inputs can include a local wiki snapshot and the extracted Silksong game text.
The default embedding backend is a deterministic local hash embedder so the
pipeline can be smoke-tested offline. Use ``--embedding-backend bge-m3`` for
the thesis configuration once the BGE-M3 model is available locally.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import chromadb


DEFAULT_VERSIONS_DIR = Path("data/processed/silksong_versions")
DEFAULT_WIKI_JSONL = Path("data/raw/silksong_wiki/pages.jsonl")
DEFAULT_EVIDENCE_JSONL = Path("data/processed/luna_knowledge_base/evidence.jsonl")
DEFAULT_DB_DIR = Path("data/vector_db/luna_lore_chroma")
DEFAULT_COLLECTION = "luna_lore_evidence"
CSV_TEXT_COLUMNS = {
    "Song_EN_ZH.csv": "EN_Song",
    "UI_EN_ZH.csv": "EN_UI",
    "Achievements_EN_ZH.csv": "EN_Achievements",
    "Credits_List_EN_ZH.csv": "EN_Credits_List",
}


@dataclass
class EvidenceDocument:
    evidence_id: str
    text: str
    metadata: dict[str, str | int | float | bool]


def read_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\u00a0", " "))
    return text.strip()


def chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks


def wiki_documents(path: Path, chunk_chars: int, overlap_chars: int) -> list[EvidenceDocument]:
    docs: list[EvidenceDocument] = []
    for page in read_jsonl(path):
        base_id = page["evidence_id"]
        title = page["title"]
        url = page.get("url", "")
        categories = "; ".join(page.get("categories", []))
        for idx, chunk in enumerate(chunk_text(page.get("text", ""), chunk_chars, overlap_chars)):
            docs.append(
                EvidenceDocument(
                    evidence_id=f"{base_id}:chunk:{idx:03d}",
                    text=f"{title}\n\n{chunk}",
                    metadata={
                        "source_type": "wiki",
                        "title": title,
                        "url": url,
                        "categories": categories,
                        "chunk_index": idx,
                    },
                )
            )
    return docs


def game_text_documents(versions_dir: Path) -> list[EvidenceDocument]:
    docs: list[EvidenceDocument] = []
    for version_dir in sorted(p for p in versions_dir.iterdir() if p.is_dir()):
        csv_dir = version_dir / "csv"
        if not csv_dir.exists():
            continue
        for csv_name, text_column in CSV_TEXT_COLUMNS.items():
            path = csv_dir / csv_name
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    key = (row.get("key") or "").strip()
                    source = clean_text(row.get(text_column) or "")
                    if not key or not source:
                        continue
                    corpus = csv_name.replace("_EN_ZH.csv", "")
                    evidence_id = f"game:{version_dir.name}:{corpus}:{key}"
                    docs.append(
                        EvidenceDocument(
                            evidence_id=evidence_id,
                            text=source,
                            metadata={
                                "source_type": "game_text",
                                "version": version_dir.name,
                                "corpus": corpus,
                                "key": key,
                            },
                        )
                    )
    return docs


def curated_documents(path: Path) -> list[EvidenceDocument]:
    docs: list[EvidenceDocument] = []
    for row in read_jsonl(path):
        text = clean_text(row.get("text", ""))
        evidence_id = row.get("evidence_id")
        if not evidence_id or not text:
            continue
        metadata = {
            key: value
            for key, value in row.items()
            if key not in {"text", "translations"} and isinstance(value, (str, int, float, bool))
        }
        if "versions" in row and isinstance(row["versions"], list):
            metadata["versions"] = "; ".join(row["versions"])
        if "categories" in row and isinstance(row["categories"], list):
            metadata["categories"] = "; ".join(row["categories"])
        docs.append(EvidenceDocument(evidence_id=evidence_id, text=text, metadata=metadata))
    return docs


def tokenise(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_']+|[\u4e00-\u9fff]", text.lower())


def hash_embeddings(texts: list[str], dimensions: int) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * dimensions
        for token in tokenise(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % dimensions
            sign = 1.0 if (value >> 63) == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        vectors.append([v / norm for v in vector])
    return vectors


def bge_m3_embeddings(texts: list[str], model_name: str, batch_size: int) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, trust_remote_code=True)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return vectors.tolist()


def embed_texts(
    texts: list[str],
    backend: str,
    model_name: str,
    batch_size: int,
    hash_dimensions: int,
) -> list[list[float]]:
    if backend == "hash":
        return hash_embeddings(texts, hash_dimensions)
    if backend == "bge-m3":
        return bge_m3_embeddings(texts, model_name, batch_size)
    raise ValueError(f"Unsupported embedding backend: {backend}")


def add_in_batches(collection, docs: list[EvidenceDocument], embeddings: list[list[float]], batch_size: int) -> None:
    for start in range(0, len(docs), batch_size):
        end = start + batch_size
        batch = docs[start:end]
        collection.add(
            ids=[doc.evidence_id for doc in batch],
            documents=[doc.text for doc in batch],
            metadatas=[doc.metadata for doc in batch],
            embeddings=embeddings[start:end],
        )


def write_manifest(
    db_dir: Path,
    docs: list[EvidenceDocument],
    collection_name: str,
    embedding_backend: str,
    model_name: str,
    hash_dimensions: int,
    wiki_jsonl: Path,
    evidence_jsonl: Path | None,
    include_game_text: bool,
) -> None:
    source_counts: dict[str, int] = {}
    for doc in docs:
        source = str(doc.metadata.get("source_type", "unknown"))
        source_counts[source] = source_counts.get(source, 0) + 1
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "collection": collection_name,
        "document_count": len(docs),
        "source_counts": source_counts,
        "embedding_backend": embedding_backend,
        "embedding_model": model_name if embedding_backend == "bge-m3" else None,
        "hash_dimensions": hash_dimensions if embedding_backend == "hash" else None,
        "wiki_snapshot": str(wiki_jsonl).replace("\\", "/"),
        "curated_evidence": str(evidence_jsonl).replace("\\", "/") if evidence_jsonl else None,
        "include_game_text": include_game_text,
    }
    db_dir.mkdir(parents=True, exist_ok=True)
    (db_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-jsonl", type=Path, default=DEFAULT_WIKI_JSONL)
    parser.add_argument("--evidence-jsonl", type=Path, default=DEFAULT_EVIDENCE_JSONL)
    parser.add_argument("--use-curated", action="store_true")
    parser.add_argument("--versions-dir", type=Path, default=DEFAULT_VERSIONS_DIR)
    parser.add_argument("--db-dir", type=Path, default=DEFAULT_DB_DIR)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--chunk-chars", type=int, default=900)
    parser.add_argument("--overlap-chars", type=int, default=120)
    parser.add_argument("--include-game-text", action="store_true")
    parser.add_argument("--embedding-backend", choices=["hash", "bge-m3"], default="hash")
    parser.add_argument("--model-name", default="BAAI/bge-m3")
    parser.add_argument("--hash-dimensions", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    if args.use_curated:
        docs = curated_documents(args.evidence_jsonl)
    else:
        docs = wiki_documents(args.wiki_jsonl, args.chunk_chars, args.overlap_chars)
        if args.include_game_text:
            docs.extend(game_text_documents(args.versions_dir))
    if not docs:
        raise SystemExit("No evidence documents found. Fetch wiki pages or include game text first.")

    client = chromadb.PersistentClient(path=str(args.db_dir))
    try:
        client.delete_collection(args.collection)
    except Exception:
        pass
    collection = client.create_collection(
        name=args.collection,
        metadata={"hnsw:space": "cosine"},
    )
    embeddings = embed_texts(
        [doc.text for doc in docs],
        args.embedding_backend,
        args.model_name,
        args.batch_size,
        args.hash_dimensions,
    )
    add_in_batches(collection, docs, embeddings, args.batch_size)
    write_manifest(
        args.db_dir,
        docs,
        args.collection,
        args.embedding_backend,
        args.model_name,
        args.hash_dimensions,
        args.wiki_jsonl,
        args.evidence_jsonl if args.use_curated else None,
        args.include_game_text,
    )


if __name__ == "__main__":
    main()
