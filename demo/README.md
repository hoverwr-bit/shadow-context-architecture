# Minimal Shadow Lifecycle Demo

This reference demo validates the **workflow contract**, not model quality or secure sandboxing. It uses only the Python standard library and a deterministic mock shadow process.

## Requirements

- Python 3.10+
- No third-party packages

## Run it

From the repository root:

```bash
PYTHONPATH=demo python -m shadow_demo init --workspace ./.shadow-demo
PYTHONPATH=demo python -m shadow_demo prepare --workspace ./.shadow-demo --task TASK-001
```

Copy the printed run directory, then execute:

```bash
PYTHONPATH=demo python -m shadow_demo run --run-dir ./.shadow-demo/runs/TASK-001/<RUN_ID>
PYTHONPATH=demo python -m shadow_demo inspect --run-dir ./.shadow-demo/runs/TASK-001/<RUN_ID>
PYTHONPATH=demo python -m shadow_demo accept --workspace ./.shadow-demo --run-dir ./.shadow-demo/runs/TASK-001/<RUN_ID>
```

The last command only previews proposed changes. To explicitly apply them:

```bash
PYTHONPATH=demo python -m shadow_demo accept --workspace ./.shadow-demo --run-dir ./.shadow-demo/runs/TASK-001/<RUN_ID> --yes
```

Run tests:

```bash
PYTHONPATH=demo python -m unittest discover -s demo/tests -v
```

## Runtime adapter (experimental)

The first provider adapter is implemented in `shadow_demo.runtime.OpenAIResponsesAdapter`. It is currently a separately tested adapter contract; the default CLI lifecycle still uses the deterministic mock runner.

A side-effect-free request can be built from a prepared package:

```python
import json
from pathlib import Path
from shadow_demo.runtime import OpenAIResponsesAdapter

adapter = OpenAIResponsesAdapter(
    model="gpt-6",
    prompt_cache_key="shadow-demo:your-workspace:v1",
)
request_body = adapter.build_request_from_file(
    Path(".shadow-demo/runs/TASK-001/<RUN_ID>/input/task_package.json")
)
print(json.dumps(request_body, indent=2))
```

Only an explicit call to `adapter.execute(package)` sends a billable API request. It requires `OPENAI_API_KEY`; no key is stored in the project or task package. The initial adapter exposes no model tools and does not feed previous Shadow outputs into a new run.

The request uses an explicit cache breakpoint on the stable developer content, followed by the changing task/project content. Keep the configured cache key stable at workspace level; do not put run IDs or task IDs in it. See [Runtime Adapter Contract](../RUNTIME_ADAPTER.md).

## What this proves

- Each `prepare` call creates a new run ID and a task-specific snapshot.
- The mock shadow is launched as a separate operating-system process.
- The runner receives a serialized task package rather than a previous conversation transcript.
- The result is a bounded `shadow-return-v1` package.
- Proposed project changes are preview-only until explicitly accepted.
- Acceptance rejects stale results if a project file changed after the task snapshot, preventing an older Shadow result from silently overwriting newer project state.
- Snapshot file hashes and an acceptance audit are recorded.
- Stable prompt rules are placed before dynamic task/project state; their exact prefix hash is recorded so prefix stability can be tested independently of actual provider cache hits.
- A regression test plants a marker in one shadow's return trace and verifies that a later task package does not inherit it.
- The provider adapter has unit tests for request construction, explicit breakpoint placement, cache-key stability, telemetry extraction, and cross-run identity rejection.

## What this does not prove

- The mock runner does not call an LLM or external tools.
- The OpenAI adapter has not yet been used for a live API call or a cache experiment.
- A subprocess is **not** a security sandbox. It runs under the same OS user and may have access to files allowed to that user. Production isolation requires an explicitly configured container/VM, filesystem and network policy, credential scoping, and provider/session controls.
- The demo does not measure prompt-cache hits. It records stable-prefix and dynamic-suffix hashes/byte lengths, but reports cache status as `not_measured`; real cache metrics must come from provider telemetry. A stable prefix is a cache-eligibility design choice, not evidence of a cache hit.
- `store=false` in the API request controls response storage behavior; it is not a claim that all provider-side retention is disabled.
- The demo does not provide a multi-file transactional database; the stale-write check is optimistic concurrency control for this local reference workflow.
- A fresh process does not automatically mean all external state is fresh. Tool sessions, provider memory, shared filesystems, and external services require separate isolation tests.
