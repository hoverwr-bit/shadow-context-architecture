# Stable Runtime Rules

- Treat the task package as the complete authorized task input.
- Do not infer missing project facts; report uncertainty explicitly.
- Separate observed evidence, assumptions, and recommendations.
- Return only one valid JSON object. Do not wrap it in Markdown fences or add prose outside the JSON.
- Do not include private reasoning, hidden chain-of-thought, or a conversation transcript. Return concise findings and evidence only.
- Do not claim that proposed project changes were applied. They are proposals for cockpit review.

## Required Return Contract: shadow-return-v1

Every return must include these keys:

- `schema_version`: exactly `shadow-return-v1`.
- `task_id`: copy the exact task ID from the task package.
- `run_id`: copy the exact run ID from the task package.
- `snapshot_id`: copy the exact snapshot ID from the manifest.
- `status`: one of `completed`, `partial`, or `failed`.
- `result`: concise outcome string.
- `findings`: array of objects with `claim` and `evidence` (array of strings). Cite file paths and snapshot hashes when relevant.
- `assumptions`: array of explicit assumptions; use an empty array when none.
- `limitations`: array of relevant limitations.
- `open_questions`: array of unresolved questions.
- `artifacts`: array of artifact descriptors; use an empty array when none.
- `proposed_project_updates`: array of objects with relative `path`, complete proposed `content`, and `summary`. Never write project files directly.
- `tests`: array describing checks actually performed; do not claim checks that were not run.
- `metrics`: object for provider/runtime telemetry when available; use an empty object when unavailable.

Return only the declared structured result schema.