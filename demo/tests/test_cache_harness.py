from __future__ import annotations

import unittest

from shadow_demo.cache_harness import build_case_request, build_experiment_plan, summarize_records


class CacheHarnessTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_experiment_plan(
            stable_prefix="Stable policy and conventions. " * 120,
            dynamic_suffix="Task state changes on every run.",
            model="test-model", base_cache_key="workspace-cache-v1", repeats=2,
        )

    def test_plan_has_five_arms_and_fresh_run_ids(self):
        self.assertEqual(len(self.plan["cases"]), 10)
        self.assertEqual({c["arm"] for c in self.plan["cases"]}, {"K0", "K1", "K2", "K3", "K4"})
        ids = [c["run_id"] for c in self.plan["cases"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_k2_prefix_is_stable_while_suffix_changes(self):
        cases = [c for c in self.plan["cases"] if c["arm"] == "K2"]
        self.assertEqual(cases[0]["stable_prefix"], cases[1]["stable_prefix"])
        self.assertNotEqual(cases[0]["dynamic_suffix"], cases[1]["dynamic_suffix"])

    def test_k2_uses_explicit_breakpoint_and_stable_key(self):
        case = next(c for c in self.plan["cases"] if c["arm"] == "K2")
        request = build_case_request(self.plan, case)
        self.assertEqual(request["prompt_cache_options"]["mode"], "explicit")
        self.assertEqual(request["prompt_cache_key"], "workspace-cache-v1-K2")
        self.assertEqual(request["input"][0]["content"][0]["prompt_cache_breakpoint"], {"mode": "explicit"})

    def test_k3_uses_per_run_keys(self):
        cases = [c for c in self.plan["cases"] if c["arm"] == "K3"]
        self.assertNotEqual(cases[0]["cache_key"], cases[1]["cache_key"])

    def test_k4_changes_prefix_and_compares_to_k2(self):
        k2 = next(c for c in self.plan["cases"] if c["arm"] == "K2")
        k4 = next(c for c in self.plan["cases"] if c["arm"] == "K4")
        self.assertNotEqual(k2["stable_prefix"], k4["stable_prefix"])
        self.assertEqual(k2["cache_key"], k4["cache_key"])
        self.assertEqual(k4["comparison_from"], "K2:last")

    def test_k0_mixes_prompt_and_has_no_cache_controls(self):
        case = next(c for c in self.plan["cases"] if c["arm"] == "K0")
        request = build_case_request(self.plan, case)
        self.assertEqual(len(request["input"]), 1)
        self.assertNotIn("prompt_cache_key", request)
        self.assertNotIn("prompt_cache_options", request)

    def test_summary_aggregates_provider_usage(self):
        records = [
            {"arm": "K2", "status": "completed", "input_tokens": 1500, "cached_tokens": 1000,
             "cache_write_tokens": 500, "elapsed_ms": 200, "cache_diagnostics": {"type": "cache_hit"}},
            {"arm": "K2", "status": "completed", "input_tokens": 1600, "cached_tokens": 1200,
             "cache_write_tokens": 0, "elapsed_ms": 180, "cache_diagnostics": {"type": "cache_hit"}},
        ]
        result = summarize_records(records)["arms"]["K2"]
        self.assertEqual(result["input_tokens"], 3100)
        self.assertEqual(result["cached_tokens"], 2200)
        self.assertAlmostEqual(result["cache_hit_ratio"], 2200 / 3100)
        self.assertEqual(result["diagnostics"], {"cache_hit": 2})

    def test_missing_usage_is_not_invented(self):
        result = summarize_records([{"arm": "K0", "status": "completed", "elapsed_ms": 100}])["arms"]["K0"]
        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["cached_tokens"])
        self.assertIsNone(result["cache_hit_ratio"])


if __name__ == "__main__":
    unittest.main()
