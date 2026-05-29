"""Query LUNA's local Chroma lore vector database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb

from build_lore_vector_db import (
    DEFAULT_COLLECTION,
    DEFAULT_DB_DIR,
    bge_m3_embeddings,
    hash_embeddings,
)


def embed_query(args: argparse.Namespace) -> list[float]:
    if args.embedding_backend == "hash":
        return hash_embeddings([args.query], args.hash_dimensions)[0]
    if args.embedding_backend == "bge-m3":
        return bge_m3_embeddings([args.query], args.model_name, 1)[0]
    raise ValueError(args.embedding_backend)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--db-dir", type=Path, default=DEFAULT_DB_DIR)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--embedding-backend", choices=["hash", "bge-m3"], default="hash")
    parser.add_argument("--model-name", default="BAAI/bge-m3")
    parser.add_argument("--hash-dimensions", type=int, default=1024)
    parser.add_argument("--source-type", choices=["wiki", "game_text"])
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(args.db_dir))
    collection = client.get_collection(args.collection)
    where = {"source_type": args.source_type} if args.source_type else None
    result = collection.query(
        query_embeddings=[embed_query(args)],
        n_results=args.top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    rows = []
    for idx, evidence_id in enumerate(result["ids"][0]):
        rows.append(
            {
                "rank": idx + 1,
                "evidence_id": evidence_id,
                "distance": result["distances"][0][idx],
                "metadata": result["metadatas"][0][idx],
                "preview": result["documents"][0][idx][:500],
            }
        )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
