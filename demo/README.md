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

## What this proves

- Each `prepare` call creates a new run ID and a task-specific snapshot.
- The shadow is launched as a separate operating-system process.
- The runner receives a serialized task package rather than a previous conversation transcript.
- The result is a bounded `shadow-return-v1` package.
- Proposed project changes are preview-only until explicitly accepted.
- Snapshot file hashes and an acceptance audit are recorded.
- Stable prompt rules are placed before dynamic task/project state; their exact prefix hash is recorded so prefix stability can be tested independently of actual provider cache hits.
- A regression test plants a marker in one shadow's return trace and verifies that a later task package does not inherit it.

## What this does not prove

- The mock runner does not call an LLM or external tools.
- A subprocess is **not** a security sandbox. It runs under the same OS user and may have access to files allowed to that user. Production isolation requires an explicitly configured container/VM, filesystem and network policy, credential scoping, and provider/session controls.
- The demo does not measure prompt-cache hits. It records stable-prefix and dynamic-suffix hashes/byte lengths, but reports cache status as `not_measured`; real cache metrics must come from provider telemetry. A stable prefix is a cache-eligibility design choice, not evidence of a cache hit.
- A fresh process does not automatically mean all external state is fresh. Tool sessions, provider memory, shared filesystems, and external services require separate isolation tests.

## Replacing the mock runner

Keep the task and return schemas. Replace `shadow_demo.runner.execute` with an adapter that invokes a chosen agent runtime in a newly provisioned execution environment. The adapter must receive only the prepared package and explicit permissions, and must emit the same bounded return schema. Do not pass the cockpit transcript or a previous shadow transcript as implicit context.
