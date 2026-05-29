"""Run one LUNA LangGraph evaluation from the command line."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from luna.config import DeepSeekConfig, LunaPaths, RetrievalConfig
from luna.graph import build_luna_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", default="manual")
    parser.add_argument("--source-en", required=True)
    parser.add_argument("--candidate-zh", required=True)
    parser.add_argument("--embedding-backend", choices=["hash", "bge-m3"], default="hash")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic scaffold nodes.")
    parser.add_argument("--no-rag", action="store_true", help="Do not retrieve local evidence.")
    parser.add_argument("--routing-threshold", type=float, default=0.45)
    parser.add_argument("--low-score-threshold", type=float, default=2.0)
    parser.add_argument("--low-average-threshold", type=float, default=2.5)
    parser.add_argument("--preliminary-model", default="deepseek-v4-flash")
    parser.add_argument("--deep-audit-model", default="deepseek-v4-pro")
    parser.add_argument("--save-log", action="store_true")
    args = parser.parse_args()

    paths = LunaPaths()
    deepseek_config = DeepSeekConfig(
        preliminary_model=args.preliminary_model,
        deep_audit_model=args.deep_audit_model,
        use_llm=not args.no_llm,
        routing_threshold=args.routing_threshold,
        low_score_threshold=args.low_score_threshold,
        low_average_threshold=args.low_average_threshold,
    )
    graph = build_luna_graph(
        paths,
        RetrievalConfig(embedding_backend=args.embedding_backend),
        deepseek_config,
        use_retrieval=not args.no_rag,
    )
    result = graph.invoke(
        {
            "sample_id": args.sample_id,
            "source_en": args.source_en,
            "candidate_zh": args.candidate_zh,
        }
    )
    print(json.dumps(result["final_report"], ensure_ascii=False, indent=2))

    if args.save_log:
        paths.run_log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = paths.run_log_dir / f"{args.sample_id}_{timestamp}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
