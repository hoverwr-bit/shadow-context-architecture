"""Provider adapters for ephemeral Shadow execution.

The OpenAI adapter is deliberately explicit: building a request is side-effect
free; execute() performs a billable network call only when directly invoked.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RuntimeAdapter(Protocol):
    def build_request(self, package: dict[str, Any]) -> dict[str, Any]: ...
    def execute(self, package: dict[str, Any]) -> dict[str, Any]: ...


class OpenAIResponsesAdapter:
    """Minimal Responses API adapter; no tools or cross-run state are enabled."""

    def __init__(
        self,
        *,
        model: str,
        prompt_cache_key: str,
        api_key_env: str = "OPENAI_API_KEY",
        timeout_seconds: int = 90,
        max_output_tokens: int = 4000,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if not prompt_cache_key.strip():
            raise ValueError("prompt_cache_key must be a stable, non-empty workspace key")
        self.model = model
        self.prompt_cache_key = prompt_cache_key
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens

    def build_request(self, package: dict[str, Any]) -> dict[str, Any]:
        prompt = package["prompt"]
        stable_prefix = prompt["stable_prefix"]
        dynamic_suffix = prompt["dynamic_suffix"]
        if not isinstance(stable_prefix, str) or not isinstance(dynamic_suffix, str):
            raise ValueError("task package prompt prefix and suffix must be strings")

        # The explicit breakpoint is attached to the final stable input content
        # block. Dynamic task/project state is placed after it in a new message.
        stable_content = {
            "type": "input_text",
            "text": stable_prefix,
            "prompt_cache_breakpoint": {"mode": "explicit", "ttl": "30m"},
        }
        dynamic_content = {"type": "input_text", "text": dynamic_suffix}
        return {
            "model": self.model,
            "input": [
                {"role": "developer", "content": [stable_content]},
                {"role": "user", "content": [dynamic_content]},
            ],
            "prompt_cache_key": self.prompt_cache_key,
            "prompt_cache_options": {"mode": "explicit", "ttl": "30m"},
            "max_output_tokens": self.max_output_tokens,
            "store": False,
            "text": {"format": {"type": "json_object"}},
        }

    def execute_raw_request(self, request_body: dict[str, Any]) -> tuple[dict[str, Any], float]:
        """Send an already-built Responses API request and return raw response + latency."""
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{self.api_key_env} is not set; request was not sent"
            )

        payload = json.dumps(request_body).encode("utf-8")
        request = Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"OpenAI Responses API request failed: {exc}") from exc

        elapsed_ms = round((time.monotonic() - started) * 1000, 2)
        return raw, elapsed_ms

    def execute(self, package: dict[str, Any]) -> dict[str, Any]:
        """Perform one API request. This method may incur usage charges."""
        raw, elapsed_ms = self.execute_raw_request(self.build_request(package))
        return self.normalize_response(raw, package, elapsed_ms=elapsed_ms)

    def normalize_response(
        self,
        response: dict[str, Any],
        package: dict[str, Any],
        *,
        elapsed_ms: float | None = None,
    ) -> dict[str, Any]:
        if response.get("status") != "completed":
            raise RuntimeError(
                f"Provider response is not completed: {response.get('status', 'unknown')}"
            )

        text_parts: list[str] = []
        for item in response.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text_parts.append(content.get("text", ""))
        if not text_parts:
            raise ValueError("Provider response contained no output_text content")

        try:
            result = json.loads("\n".join(text_parts))
        except json.JSONDecodeError as exc:
            raise ValueError("Shadow output was not valid JSON") from exc

        required = {
            "schema_version", "task_id", "run_id", "snapshot_id", "status",
            "result", "findings", "assumptions", "limitations", "open_questions",
            "artifacts", "proposed_project_updates", "tests", "metrics",
        }
        missing = required.difference(result)
        if missing:
            raise ValueError(f"Shadow return is missing required fields: {sorted(missing)}")

        task = package["task"]
        expected = {
            "schema_version": "shadow-return-v1",
            "task_id": task["task_id"],
            "run_id": package["run_id"],
            "snapshot_id": package["manifest"]["snapshot_id"],
        }
        for key, value in expected.items():
            if result.get(key) != value:
                raise ValueError(f"Shadow return identity mismatch for {key}")
        if result["status"] not in {"completed", "partial", "failed"}:
            raise ValueError("Shadow return has an unsupported status")

        usage = response.get("usage") or {}
        input_details = usage.get("input_tokens_details") or {}
        metrics = result.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}
        metrics["runtime"] = {
            "provider": "openai",
            "model": response.get("model", self.model),
            "response_id": response.get("id"),
            "elapsed_ms": elapsed_ms,
            "input_tokens": usage.get("input_tokens"),
            "cached_tokens": input_details.get("cached_tokens"),
            "cache_write_tokens": input_details.get("cache_write_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "cost": "not_computed",
        }
        metrics["prompt_cache"] = {
            "status": "measured" if input_details else "not_available",
            "stable_prefix_sha256": hashlib.sha256(
                package["prompt"]["stable_prefix"].encode("utf-8")
            ).hexdigest(),
            "dynamic_suffix_sha256": hashlib.sha256(
                package["prompt"]["dynamic_suffix"].encode("utf-8")
            ).hexdigest(),
            "cached_tokens": input_details.get("cached_tokens"),
            "cache_write_tokens": input_details.get("cache_write_tokens"),
            "cache_key": self.prompt_cache_key,
            "breakpoint_mode": "explicit",
        }
        result["metrics"] = metrics
        return result

    def build_request_from_file(self, package_path: Path) -> dict[str, Any]:
        """Convenience helper for dry-run tooling; performs no network request."""
        package = json.loads(package_path.read_text(encoding="utf-8"))
        return self.build_request(package)
