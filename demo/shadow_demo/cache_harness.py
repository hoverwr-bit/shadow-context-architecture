"""Controlled prompt-cache experiment planner and runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shadow_demo.runtime import OpenAIResponsesAdapter


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content(text: str, breakpoint: bool = False) -> dict[str, Any]:
    item: dict[str, Any] = {"type": "input_text", "text": text}
    if breakpoint:
        item["prompt_cache_breakpoint"] = {"mode": "explicit"}
    return item


def build_experiment_plan(*, stable_prefix: str, dynamic_suffix: str, model: str,
                          base_cache_key: str, repeats: int = 3,
                          changed_prefix: str | None = None) -> dict[str, Any]:
    if not stable_prefix.strip() or not dynamic_suffix.strip():
        raise ValueError("stable_prefix and dynamic_suffix must not be empty")
    if not model.strip() or not base_cache_key.strip():
        raise ValueError("model and base_cache_key must not be empty")
    if repeats < 2 or repeats > 20:
        raise ValueError("repeats must be between 2 and 20")

    prefix_v2 = changed_prefix
    if prefix_v2 is None:
        prefix_v2 = stable_prefix.rstrip() + "\n\n[EXPERIMENT: stable-prefix-version-2]\n"

    cases: list[dict[str, Any]] = []
    for arm in ("K0", "K1", "K2", "K3"):
        for index in range(repeats):
            run_id = str(uuid.uuid4())
            suffix = (
                dynamic_suffix.rstrip()
                + f"\n\n[Experiment arm: {arm}; fresh shadow run: {run_id}]\n"
                + 'Return exactly this JSON object: {"ok": true}.'
            )
            if arm == "K0":
                layout, cache_mode, cache_key, breakpoint = "mixed", "provider_default", None, False
            elif arm == "K1":
                layout, cache_mode, cache_key, breakpoint = "split", "implicit", f"{base_cache_key}-K1", False
            elif arm == "K2":
                layout, cache_mode, cache_key, breakpoint = "split", "explicit", f"{base_cache_key}-K2", True
            else:
                layout, cache_mode, cache_key, breakpoint = "split", "explicit", f"{base_cache_key}-K3-{index + 1}", True

            cases.append({
                "case_id": f"{arm}-{index + 1:02d}", "arm": arm, "run_id": run_id,
                "stable_prefix": stable_prefix, "dynamic_suffix": suffix,
                "layout": layout, "cache_mode": cache_mode, "cache_key": cache_key,
                "breakpoint": breakpoint, "comparison_from": None,
            })

    for index in range(repeats):
        run_id = str(uuid.uuid4())
        suffix = (
            dynamic_suffix.rstrip()
            + f"\n\n[Experiment arm: K4; fresh shadow run: {run_id}]\n"
            + 'Return exactly this JSON object: {"ok": true}.'
        )
        cases.append({
            "case_id": f"K4-{index + 1:02d}", "arm": "K4", "run_id": run_id,
            "stable_prefix": prefix_v2, "dynamic_suffix": suffix,
            "layout": "split", "cache_mode": "explicit",
            "cache_key": f"{base_cache_key}-K2", "breakpoint": True,
            "comparison_from": "K2:last",
        })

    return {
        "schema_version": "shadow-cache-experiment-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model, "base_cache_key": base_cache_key, "repeats": repeats,
        "cases": cases,
    }


def build_case_request(plan: dict[str, Any], case: dict[str, Any],
                       comparison_response_id: str | None = None) -> dict[str, Any]:
    stable, dynamic = case["stable_prefix"], case["dynamic_suffix"]
    if case["layout"] == "mixed":
        messages = [{"role": "user", "content": [_content(stable + "\n" + dynamic)]}]
    elif case["breakpoint"]:
        messages = [
            {"role": "developer", "content": [_content(stable, breakpoint=True)]},
            {"role": "user", "content": [_content(dynamic)]},
        ]
    else:
        messages = [
            {"role": "developer", "content": [_content(stable)]},
            {"role": "user", "content": [_content(dynamic)]},
        ]

    request: dict[str, Any] = {
        "model": plan["model"], "input": messages, "max_output_tokens": 40,
        "store": False, "text": {"format": {"type": "json_object"}},
    }
    if case["cache_key"]:
        request["prompt_cache_key"] = case["cache_key"]
    if case["cache_mode"] != "provider_default":
        options: dict[str, Any] = {"mode": case["cache_mode"], "ttl": "30m"}
        if comparison_response_id:
            options["comparison_response_id"] = comparison_response_id
        request["prompt_cache_options"] = options
    return request


def _number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["arm"]].append(record)

    arms: dict[str, Any] = {}
    for arm, items in sorted(grouped.items()):
        successful = [item for item in items if item.get("status") == "completed"]
        input_values = [_number(item.get("input_tokens")) for item in successful]
        cached_values = [_number(item.get("cached_tokens")) for item in successful]
        write_values = [_number(item.get("cache_write_tokens")) for item in successful]
        latency_values = [_number(item.get("elapsed_ms")) for item in successful]
        input_total = sum(v for v in input_values if v is not None)
        cached_total = sum(v for v in cached_values if v is not None)
        diagnostics: dict[str, int] = defaultdict(int)
        for item in successful:
            kind = (item.get("cache_diagnostics") or {}).get("type")
            if kind:
                diagnostics[kind] += 1
        arms[arm] = {
            "requests": len(items), "successful": len(successful),
            "failed": len(items) - len(successful),
            "input_tokens": input_total if any(v is not None for v in input_values) else None,
            "cached_tokens": cached_total if any(v is not None for v in cached_values) else None,
            "cache_hit_ratio": cached_total / input_total if input_total and any(v is not None for v in cached_values) else None,
            "cache_write_tokens": sum(v for v in write_values if v is not None) if any(v is not None for v in write_values) else None,
            "mean_latency_ms": statistics.mean(latency_values) if latency_values else None,
            "diagnostics": dict(diagnostics),
        }
    return {
        "schema_version": "shadow-cache-summary-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "arms": arms,
        "cost": "not_computed: apply the current model-specific price schedule separately",
    }


def _record_response(plan: dict[str, Any], case: dict[str, Any],
                     response: dict[str, Any], elapsed_ms: float) -> dict[str, Any]:
    usage = response.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    writes = details.get("cache_write_tokens_details") or {}
    diagnostics = response.get("prompt_cache_diagnostics") or {}
    return {
        "case_id": case["case_id"], "arm": case["arm"], "run_id": case["run_id"],
        "status": response.get("status", "unknown"), "response_id": response.get("id"),
        "model": response.get("model", plan["model"]), "elapsed_ms": elapsed_ms,
        "input_tokens": usage.get("input_tokens"), "cached_tokens": details.get("cached_tokens"),
        "cache_write_tokens": details.get("cache_write_tokens"),
        "cache_write_tokens_details": {
            "ttl_30m_tokens": writes.get("ttl_30m_tokens"),
            "ttl_12h_tokens": writes.get("ttl_12h_tokens"),
        },
        "output_tokens": usage.get("output_tokens"), "total_tokens": usage.get("total_tokens"),
        "cache_diagnostics": {
            "type": diagnostics.get("type"), "reason": diagnostics.get("reason"),
            "comparison_reusable_tokens": diagnostics.get("comparison_reusable_tokens"),
            "cache_missed_tokens": diagnostics.get("cache_missed_tokens"),
        },
        "stable_prefix_sha256": sha256_text(case["stable_prefix"]),
        "dynamic_suffix_sha256": sha256_text(case["dynamic_suffix"]),
        "cache_key": case.get("cache_key"), "cache_mode": case["cache_mode"],
        "breakpoint": case["breakpoint"], "cost": "not_computed",
    }


def run_plan(plan: dict[str, Any], output_dir: Path, *, execute: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    request_dir = output_dir / "requests"
    request_dir.mkdir(exist_ok=True)
    adapter = OpenAIResponsesAdapter(model=plan["model"], prompt_cache_key=plan["base_cache_key"])
    records: list[dict[str, Any]] = []
    latest_k2_response_id: str | None = None
    jsonl_path = output_dir / "records.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()

    for case in plan["cases"]:
        comparison_id = latest_k2_response_id if case.get("comparison_from") == "K2:last" else None
        body = build_case_request(plan, case, comparison_id)
        request_path = request_dir / f'{case["case_id"]}.json'
        request_path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        if not execute:
            continue
        try:
            response, elapsed_ms = adapter.execute_raw_request(body)
            record = _record_response(plan, case, response, elapsed_ms)
            if case["arm"] == "K2" and response.get("id"):
                latest_k2_response_id = response["id"]
        except Exception as exc:
            record = {
                "case_id": case["case_id"], "arm": case["arm"], "run_id": case["run_id"],
                "status": "error", "error": str(exc), "cache_key": case.get("cache_key"),
                "cache_mode": case["cache_mode"],
            }
        records.append(record)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    if execute:
        summary = summarize_records(records)
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        summary = {
            "status": "dry_run_only", "requests_built": len(plan["cases"]), "network_calls": 0,
            "instruction": "Re-run with --execute to send billable API requests.",
        }
        (output_dir / "dry_run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Shadow prompt-cache experiment harness")
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan", help="Create a plan without API calls")
    p_plan.add_argument("--prefix-file", type=Path, required=True)
    p_plan.add_argument("--dynamic-file", type=Path, required=True)
    p_plan.add_argument("--k4-prefix-file", type=Path)
    p_plan.add_argument("--model", required=True)
    p_plan.add_argument("--cache-key", required=True)
    p_plan.add_argument("--repeats", type=int, default=3)
    p_plan.add_argument("--output", type=Path, required=True)
    p_run = sub.add_parser("run", help="Render requests or explicitly execute a plan")
    p_run.add_argument("--plan", type=Path, required=True)
    p_run.add_argument("--output-dir", type=Path, required=True)
    p_run.add_argument("--execute", action="store_true", help="Send real, billable API requests")
    args = parser.parse_args()

    if args.command == "plan":
        changed = args.k4_prefix_file.read_text(encoding="utf-8") if args.k4_prefix_file else None
        plan = build_experiment_plan(
            stable_prefix=args.prefix_file.read_text(encoding="utf-8"),
            dynamic_suffix=args.dynamic_file.read_text(encoding="utf-8"),
            model=args.model, base_cache_key=args.cache_key,
            repeats=args.repeats, changed_prefix=changed,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Plan written: {args.output.resolve()} ({len(plan['cases'])} requests)")
    else:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        print(json.dumps(run_plan(plan, args.output_dir, execute=args.execute), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
