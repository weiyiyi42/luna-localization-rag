"""Small DeepSeek Chat Completions client for LUNA agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from luna.config import DeepSeekConfig


@dataclass
class DeepSeekResponse:
    content: str
    parsed: dict[str, Any]
    usage: dict[str, Any]
    model: str


class DeepSeekClient:
    """Minimal OpenAI-compatible DeepSeek client.

    API keys are read from the environment and never stored in project files.
    """

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        self.config = config or DeepSeekConfig()
        self.api_key = self.config.api_key
        if not self.api_key:
            raise RuntimeError(
                f"Missing DeepSeek API key. Set {self.config.api_key_env} in the environment."
            )

    def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: str,
        thinking_enabled: bool = False,
    ) -> DeepSeekResponse:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "enabled" if thinking_enabled else "disabled"},
        }
        response = requests.post(
            f"{self.config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content") or "{}"
        return DeepSeekResponse(
            content=content,
            parsed=_parse_json_object(content),
            usage=data.get("usage", {}),
            model=data.get("model", model),
        )


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"_parse_error": True, "raw_content": content}
        try:
            value = json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return {"_parse_error": True, "raw_content": content}
    if not isinstance(value, dict):
        return {"_parse_error": True, "raw_content": content}
    return value
