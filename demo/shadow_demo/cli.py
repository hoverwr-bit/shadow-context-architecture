"""CLI for preparing, running, inspecting, and accepting shadow tasks."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


def _json_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(value: str) -> Path:
    posix = PurePosixPath(value)
    if posix.is_absolute() or not posix.parts or any(part in ("..", "") for part in posix.parts):
        raise ValueError(f"Unsafe relative path: {value}")
    return Path(*posix.parts)


def init_workspace(workspace: Path) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures"
    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError(f"Workspace is not empty: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_root / "project", workspace / "project", dirs_exist_ok=True)
    shutil.copytree(fixture_root / "tasks", workspace / "tasks", dirs_exist_ok=True)
    (workspace / "runs").mkdir(exist_ok=True)
    print(f"Initialized workspace: {workspace.resolve()}")


def prepare(workspace: Path, task_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", task_id):
        raise ValueError("task_id must use 1-64 letters, digits, underscores, or hyphens")
    task_path = workspace / "tasks" / f"{task_id}.json"
    if not task_path.is_file():
        raise FileNotFoundError(f"Task not found: {task_path}")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    if task.get("task_id") != task_id or not task.get("objective"):
        raise ValueError("Task must contain matching task_id and a non-empty objective")

    run_id = str(uuid.uuid4())
    run_dir = workspace / "runs" / task_id / run_id
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True)
    project_snapshot: dict[str, str] = {}
    file_manifest: dict[str, dict[str, str]] = {}

    for relative in task.get("project_files", []):
        safe = _safe_relative(relative)
        project_root = (workspace / "project").resolve()
        source = (project_root / safe).resolve()
        if project_root not in source.parents or not source.is_file():
            raise FileNotFoundError(f"Required project file missing or outside project root: {relative}")
        raw = source.read_bytes()
        content = raw.decode("utf-8")
        project_snapshot[relative] = content
        (input_dir / safe).parent.mkdir(parents=True, exist_ok=True)
        (input_dir / safe).write_bytes(raw)
        file_manifest[relative] = {"sha256": _sha256(raw), "bytes": str(len(raw))}

    snapshot_seed = json.dumps(file_manifest, sort_keys=True).encode("utf-8")
    manifest = {
        "snapshot_id": _sha256(snapshot_seed)[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": file_manifest,
    }
    package = {
        "schema_version": "shadow-task-v1",
        "task": task,
        "run_id": run_id,
        "manifest": manifest,
        "project_snapshot": project_snapshot,
    }
    _json_write(input_dir / "task_package.json", package)
    _json_write(run_dir / "manifest.json", manifest)
    print(run_dir.resolve())
    return run_dir


def run_shadow(run_dir: Path) -> None:
    package_path = run_dir / "input" / "task_package.json"
    if not package_path.is_file():
        raise FileNotFoundError(f"Prepared task package missing: {package_path}")
    output_path = run_dir / "output" / "return.json"
    module_root = Path(__file__).resolve().parents[1]
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP") if key in os.environ}
    env["PYTHONPATH"] = str(module_root)
    command = [sys.executable, "-m", "shadow_demo.runner", "--package", str(package_path.resolve()), "--output", str(output_path.resolve())]
    completed = subprocess.run(command, cwd=run_dir, env=env, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Shadow process failed ({completed.returncode}): {completed.stderr.strip()}")
    result = json.loads(output_path.read_text(encoding="utf-8"))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "shadow-return-v1" or result.get("run_id") != package["run_id"]:
        raise ValueError("Shadow return package failed schema/run identity validation")
    print(f"Shadow finished: {result['status']} — {output_path.resolve()}")


def inspect_result(run_dir: Path) -> None:
    result_path = run_dir / "output" / "return.json"
    if not result_path.is_file():
        raise FileNotFoundError(f"Return package missing: {result_path}")
    print(result_path.read_text(encoding="utf-8"))


def accept_result(workspace: Path, run_dir: Path, yes: bool) -> None:
    result_path = run_dir / "output" / "return.json"
    if not result_path.is_file():
        raise FileNotFoundError(f"Return package missing: {result_path}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "completed":
        raise ValueError("Only completed results can be accepted")
    updates = result.get("proposed_project_updates", [])
    if not yes:
        print(json.dumps(updates, indent=2, ensure_ascii=False))
        print("\nNo files changed. Re-run with --yes to accept these updates.")
        return

    project_root = (workspace / "project").resolve()
    for update in updates:
        relative = _safe_relative(update["path"])
        target = (project_root / relative).resolve()
        if project_root not in target.parents and target != project_root:
            raise ValueError(f"Update escapes project directory: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(update["content"], encoding="utf-8")

    audit = {
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "run_id": result["run_id"],
        "snapshot_id": result["snapshot_id"],
        "accepted_paths": [item["path"] for item in updates],
    }
    _json_write(run_dir / "acceptance.json", audit)
    print(f"Accepted {len(updates)} project update(s). Audit: {run_dir / 'acceptance.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Shadow Context Architecture lifecycle demo")
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init", help="Create a demo cockpit-backed project workspace")
    p_init.add_argument("--workspace", type=Path, default=Path(".shadow-demo"))
    p_prepare = sub.add_parser("prepare", help="Create a fresh task snapshot")
    p_prepare.add_argument("--workspace", type=Path, default=Path(".shadow-demo"))
    p_prepare.add_argument("--task", required=True)
    p_run = sub.add_parser("run", help="Run one fresh mock shadow process")
    p_run.add_argument("--run-dir", type=Path, required=True)
    p_inspect = sub.add_parser("inspect", help="Inspect the structured return package")
    p_inspect.add_argument("--run-dir", type=Path, required=True)
    p_accept = sub.add_parser("accept", help="Review or explicitly accept proposed project updates")
    p_accept.add_argument("--workspace", type=Path, default=Path(".shadow-demo"))
    p_accept.add_argument("--run-dir", type=Path, required=True)
    p_accept.add_argument("--yes", action="store_true", help="Apply proposed updates; without this flag, only preview")
    args = parser.parse_args()

    if args.command == "init":
        init_workspace(args.workspace)
    elif args.command == "prepare":
        prepare(args.workspace, args.task)
    elif args.command == "run":
        run_shadow(args.run_dir)
    elif args.command == "inspect":
        inspect_result(args.run_dir)
    elif args.command == "accept":
        accept_result(args.workspace, args.run_dir, args.yes)


if __name__ == "__main__":
    main()
