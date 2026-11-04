"""A deterministic mock shadow runner used to test lifecycle boundaries.

This process receives one serialized task package and emits one bounded result.
It is intentionally not an LLM agent and does not claim OS-level sandboxing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def execute(package_path: Path, output_path: Path) -> None:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    task = package["task"]
    snapshot = package["project_snapshot"]
    state = snapshot.get("STATE.md", "")
    state_hash = package["manifest"]["files"].get("STATE.md", {}).get("sha256", "unavailable")

    result = {
        "schema_version": "shadow-return-v1",
        "task_id": task["task_id"],
        "run_id": package["run_id"],
        "snapshot_id": package["manifest"]["snapshot_id"],
        "status": "completed",
        "result": f"Mock shadow completed task: {task['objective']}",
        "findings": [
            {
                "claim": "The task package contained the pinned project state.",
                "evidence": [f"STATE.md sha256:{state_hash}"],
            }
        ],
        "assumptions": ["This result was produced by the deterministic mock runner."],
        "limitations": ["No model inference, external tools, or secure OS sandbox were used."],
        "open_questions": [],
        "artifacts": [],
        "proposed_project_updates": [
            {
                "path": "STATE.md",
                "content": state.rstrip()
                + "\n\n## Demo execution record\n"
                + f"- Completed mock task `{task['task_id']}` in run `{package['run_id']}`.\n",
                "summary": "Append a traceable mock execution record.",
            }
        ],
        "tests": [],
        "metrics": {
            "runner": "mock",
            "prompt_cache": {
                "status": "not_measured",
                "reason": "The mock runner does not call a model provider.",
                "stable_prefix_sha256": package["prompt_layout"]["stable_prefix_sha256"],
                "dynamic_suffix_sha256": package["prompt_layout"]["dynamic_suffix_sha256"],
                "stable_prefix_bytes": package["prompt_layout"]["stable_prefix_bytes"],
                "dynamic_suffix_bytes": package["prompt_layout"]["dynamic_suffix_bytes"],
            },
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    execute(args.package, args.output)


if __name__ == "__main__":
    main()
