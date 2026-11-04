from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shadow_demo.cli import accept_result, init_workspace, prepare, run_shadow


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / "workspace"
        init_workspace(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_each_prepare_creates_a_new_run_and_snapshot_package(self):
        first = prepare(self.workspace, "TASK-001")
        second = prepare(self.workspace, "TASK-001")
        self.assertNotEqual(first.name, second.name)
        first_package = json.loads((first / "input" / "task_package.json").read_text())
        second_package = json.loads((second / "input" / "task_package.json").read_text())
        self.assertNotEqual(first_package["run_id"], second_package["run_id"])
        self.assertEqual(first_package["manifest"]["snapshot_id"], second_package["manifest"]["snapshot_id"])
        self.assertEqual(set(first_package["project_snapshot"]), {"STATE.md", "DECISIONS.md"})

    def test_stable_prefix_survives_project_state_changes(self):
        first = prepare(self.workspace, "TASK-001")
        first_package = json.loads((first / "input" / "task_package.json").read_text())
        stable_prefix = first_package["prompt"]["stable_prefix"]
        self.assertTrue(first_package["prompt"]["rendered"].startswith(stable_prefix))

        state_file = self.workspace / "project" / "STATE.md"
        state_file.write_text(state_file.read_text() + "\n- New progress update.\n")
        second = prepare(self.workspace, "TASK-001")
        second_package = json.loads((second / "input" / "task_package.json").read_text())

        self.assertEqual(
            first_package["prompt_layout"]["stable_prefix_sha256"],
            second_package["prompt_layout"]["stable_prefix_sha256"],
        )
        self.assertNotEqual(
            first_package["prompt_layout"]["dynamic_suffix_sha256"],
            second_package["prompt_layout"]["dynamic_suffix_sha256"],
        )
        self.assertEqual(first_package["prompt_layout"]["cache_status"], "not_measured")

    def test_shadow_runs_as_a_separate_process_and_returns_bounded_result(self):
        run_dir = prepare(self.workspace, "TASK-001")
        run_shadow(run_dir)
        result = json.loads((run_dir / "output" / "return.json").read_text())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["schema_version"], "shadow-return-v1")
        self.assertIn("findings", result)
        self.assertNotIn("transcript", result)
        self.assertEqual(result["metrics"]["prompt_cache"]["status"], "not_measured")

    def test_later_shadow_does_not_receive_prior_shadow_return_trace(self):
        first = prepare(self.workspace, "TASK-001")
        run_shadow(first)
        marker = "PRIVATE_PRIOR_SHADOW_TRACE_7f3a"
        first_return = first / "output" / "return.json"
        first_return.write_text(first_return.read_text() + marker)

        second = prepare(self.workspace, "TASK-001")
        package_text = (second / "input" / "task_package.json").read_text()
        self.assertNotIn(marker, package_text)
        self.assertFalse((second / "input" / "prior_return.json").exists())

    def test_proposed_update_is_not_applied_without_explicit_acceptance(self):
        run_dir = prepare(self.workspace, "TASK-001")
        run_shadow(run_dir)
        before = (self.workspace / "project" / "STATE.md").read_text()
        accept_result(self.workspace, run_dir, yes=False)
        after = (self.workspace / "project" / "STATE.md").read_text()
        self.assertEqual(before, after)
        self.assertFalse((run_dir / "acceptance.json").exists())

    def test_explicit_acceptance_updates_project_and_writes_audit(self):
        run_dir = prepare(self.workspace, "TASK-001")
        run_shadow(run_dir)
        accept_result(self.workspace, run_dir, yes=True)
        updated = (self.workspace / "project" / "STATE.md").read_text()
        self.assertIn("Demo execution record", updated)
        audit = json.loads((run_dir / "acceptance.json").read_text())
        self.assertEqual(audit["accepted_paths"], ["STATE.md"])

    def test_path_traversal_is_rejected(self):
        from shadow_demo.cli import _safe_relative
        with self.assertRaises(ValueError):
            _safe_relative("../../outside.txt")


if __name__ == "__main__":
    unittest.main()
