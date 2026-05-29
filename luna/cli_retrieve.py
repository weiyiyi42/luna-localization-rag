"""Command-line evidence retrieval for the local LUNA vector database."""

from __future__ import annotations

import argparse
import json

from luna.config import LunaPaths, RetrievalConfig
from luna.retriever import LunaRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--source-type")
    parser.add_argument("--min-trust-level", type=int, default=1)
    parser.add_argument("--embedding-backend", choices=["hash", "bge-m3"], default="hash")
    args = parser.parse_args()

    paths = LunaPaths()
    config = RetrievalConfig(
        embedding_backend=args.embedding_backend,
        top_k=args.top_k,
        min_trust_level=args.min_trust_level,
    )
    retriever = LunaRetriever(paths.vector_db_dir, paths.collection_name, config)
    results = retriever.search(args.query, source_type=args.source_type)
    print(
        json.dumps(
            [
                {
                    "rank": idx + 1,
                    "evidence_id": item.evidence_id,
                    "distance": item.distance,
                    "source_type": item.metadata.get("source_type"),
                    "trust_level": item.metadata.get("trust_level"),
                    "preview": item.text[:400],
                }
                for idx, item in enumerate(results)
            ],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

