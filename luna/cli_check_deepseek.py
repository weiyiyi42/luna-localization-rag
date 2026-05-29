"""Check whether the DeepSeek API key and model connection work."""

from __future__ import annotations

import argparse
import json

from luna.config import DeepSeekConfig
from luna.deepseek_client import DeepSeekClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="deepseek-v4-flash")
    args = parser.parse_args()

    client = DeepSeekClient(DeepSeekConfig(max_tokens=200))
    response = client.chat_json(
        model=args.model,
        system="Return valid JSON only.",
        user='Return {"ok": true, "message": "connected"}',
        thinking_enabled=False,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "model": response.model,
                "response": response.parsed,
                "usage": response.usage,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
