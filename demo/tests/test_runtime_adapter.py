from __future__ import annotations

import unittest

from shadow_demo.runtime import OpenAIResponsesAdapter
from shadow_demo.cli import build_openai_request, init_workspace, prepare


def sample_package():
    return {
        "task": {"task_id": "TASK-001"},
        "run_id": "run-123",
        "manifest": {"snapshot_id": "snap-123"},
        "prompt": {
            "stable_prefix": "Stable rules\n",
            "dynamic_suffix": "Task state changes each run\n",
        },
    }


class OpenAIAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = OpenAIResponsesAdapter(
            model="gpt-6",
            prompt_cache_key="shadow-demo:workspace-alpha:v1",
        )

    def test_cli_dry_run_builds_request_from_prepared_package_without_network(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            init_workspace(workspace)
            run_dir = prepare(workspace, "TASK-001")
            output_path = Path(tmp) / "request" / "body.json"
            request = build_openai_request(
                run_dir,
                "test-model",
                "workspace-stable-key",
                output_path,
            )
            saved = __import__("json").loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(request, saved)
            self.assertEqual(saved["prompt_cache_key"], "workspace-stable-key")

    def test_request_places_explicit_breakpoint_before_dynamic_suffix(self):
        request = self.adapter.build_request(sample_package())
        self.assertEqual(request["prompt_cache_options"]["mode"], "explicit")
        self.assertEqual(request["prompt_cache_key"], "shadow-demo:workspace-alpha:v1")
        self.assertEqual(request["input"][0]["content"][0]["text"], "Stable rules\n")
        self.assertEqual(
            request["input"][0]["content"][0]["prompt_cache_breakpoint"],
            {"mode": "explicit", "ttl": "30m"},
        )
        self.assertEqual(request["input"][1]["content"][0]["text"], "Task state changes each run\n")
        self.assertFalse(request["store"])
        self.assertEqual(request["text"]["format"]["type"], "json_object")

    def test_request_builder_is_deterministic_across_fresh_runs(self):
        first = self.adapter.build_request(sample_package())
        second_package = sample_package()
        second_package["run_id"] = "run-456"
        second = self.adapter.build_request(second_package)
        self.assertEqual(first, second)

    def test_cache_key_must_be_explicit_and_non_empty(self):
        with self.assertRaises(ValueError):
            OpenAIResponsesAdapter(model="gpt-6", prompt_cache_key=" ")

    def test_normalizer_preserves_identity_and_records_cache_usage(self):
        package = sample_package()
        body = {
            "status": "completed",
            "id": "resp-1",
            "model": "gpt-6",
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": (
                        '{"schema_version":"shadow-return-v1",'
                        '"task_id":"TASK-001","run_id":"run-123",'
                        '"snapshot_id":"snap-123","status":"completed",'
                        '"result":"ok","findings":[],"assumptions":[],'
                        '"limitations":[],"open_questions":[],"artifacts":[],'
                        '"proposed_project_updates":[],"tests":[],"metrics":{}}'
                    ),
                }],
            }],
            "usage": {
                "input_tokens": 1200,
                "input_tokens_details": {"cached_tokens": 900, "cache_write_tokens": 0},
                "output_tokens": 80,
                "total_tokens": 1280,
            },
        }
        result = self.adapter.normalize_response(body, package, elapsed_ms=42.5)
        self.assertEqual(result["schema_version"], "shadow-return-v1")
        self.assertEqual(result["metrics"]["runtime"]["cached_tokens"], 900)
        self.assertEqual(result["metrics"]["runtime"]["cache_write_tokens"], 0)
        self.assertEqual(result["metrics"]["runtime"]["cost"], "not_computed")
        self.assertEqual(result["metrics"]["prompt_cache"]["status"], "measured")

    def test_normalizer_rejects_cross_run_result(self):
        package = sample_package()
        body = {
            "status": "completed",
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": (
                        '{"schema_version":"shadow-return-v1",'
                        '"task_id":"TASK-001","run_id":"old-run",'
                        '"snapshot_id":"snap-123","status":"completed",'
                        '"result":"bad","findings":[],"assumptions":[],'
                        '"limitations":[],"open_questions":[],"artifacts":[],'
                        '"proposed_project_updates":[],"tests":[],"metrics":{}}'
                    ),
                }],
            }],
        }
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.adapter.normalize_response(body, package)


if __name__ == "__main__":
    unittest.main()
