# Implementation Plan — Shadow Context Architecture

**Status:** Working implementation baseline  
**Baseline reviewed:** 2026-11-04  
**Target branch:** `prototype/minimal-demo-v0.1`  
**Related PR:** [#1 — Add minimal runnable Shadow lifecycle demo](https://github.com/hoverwr-bit/shadow-context-architecture/pull/1)

## 1. Purpose and decision boundary

This plan turns the current architecture proposal and prototype into a reviewable, falsifiable engineering program. It is not a commitment to build a production agent platform, and it does not pre-decide the dispatch/scheduling architecture.

The central design boundary is:

- **Cockpit:** a persistent, structured, user-facing workspace. It is not an Agent, planner, parent Agent, or orchestrator.
- **Project files:** the durable source of project state, decisions, constraints, and accepted results.
- **Shadow:** a fresh, task-scoped execution context. It receives an explicit task package and returns a bounded result. It does not inherit another Shadow's transcript or tool trace.
- **Runtime:** the execution boundary that creates and contains a Shadow run. Its production implementation, dispatch policy, and scheduling responsibilities remain open design questions.

The project must not quietly reintroduce a persistent coordinating Agent under another name. If future work proposes one, it requires an explicit architecture decision and comparison against the non-Agent cockpit model.

## 2. Current baseline and evidence labels

At the review baseline, the repository contains a lifecycle reference demo, a provider adapter, a prompt-cache experiment harness, documentation, and CI tests.

Use these evidence labels consistently:

| Label | Meaning |
|---|---|
| Implemented | Code or documentation exists in the branch |
| Unit-tested | Automated tests exercise the behavior |
| CI-verified | A recorded CI run passed for a specific commit |
| Live-tested | The behavior was exercised against a real provider/environment |
| Demonstrated | Reproducible evidence supports the stated behavior |
| Hypothesis | A falsifiable claim not yet established |

Current baseline:

- The mock lifecycle demonstrates fresh subprocess execution and a bounded return contract.
- The adapter builds Responses API requests and has an explicit network execution method.
- The cache harness builds K0–K4 requests and supports dry-run; live execution has not been established by the repository evidence reviewed here.
- A subprocess running as the same OS user is **not** a security sandbox.
- `store=false` is not proof that all provider-side retention is disabled.
- Prompt-cache eligibility and request construction do not establish cache hits, cost savings, or task-quality improvements.
- A passing unit/CI suite validates only the tested code paths and commit; it does not prove the architecture hypothesis.

Do not upgrade a claim from implemented/tested to demonstrated without adding the corresponding evidence.

## 3. Work packages

### WP-01 — Architecture definition and terminology

**Goal:** Make the architectural boundary unambiguous across RFC, architecture notes, README, experiment documents, and code comments.

Tasks:
1. Define Cockpit as a persistent structured workspace, explicitly non-Agent.
2. Define project files as the durable project-state substrate.
3. Define Shadow as a fresh, task-scoped execution context with no inherited prior Shadow transcript/tool trace.
4. Define Runtime as an execution boundary, without assuming it is a planner or orchestrator.
5. Keep dispatch, scheduling, retry, and concurrency policy explicitly open until supported by a separate decision record.
6. Add a glossary and a short list of non-goals.
7. Audit all repository wording for accidental references to a main Agent, parent Agent, hidden planner, or implied persistent coordinator.

Acceptance criteria:
- All top-level documents use the same four-part vocabulary.
- No document describes Cockpit as an Agent or orchestrator.
- Open design questions are labeled as open questions, not silently presented as decisions.
- A reviewer can explain the lifecycle without relying on chat history.

### WP-02 — Complete task input manifest and snapshot identity

**Priority:** P0

**Goal:** Make every input that can affect a Shadow result traceable and immutable for the lifetime of a run.

Inputs to account for:
- Task definition and acceptance criteria.
- Project state and decision files selected for the task.
- Stable rules and project conventions.
- Explicitly authorized reference files and their versions/hashes.
- Runtime/request configuration that materially changes execution (model identifier, output contract/schema version, relevant tool/policy configuration when introduced).

Tasks:
1. Introduce a versioned `task-snapshot-manifest-v1` (or successor) schema.
2. Record each input's logical path, content hash, byte length, role/classification, and inclusion reason.
3. Compute snapshot identity from a canonical, deterministic representation of the complete manifest; do not rely only on project-state files.
4. Separate immutable task inputs from mutable workspace state.
5. Validate the manifest before execution and again before accepting a result.
6. Define behavior for missing, changed, inaccessible, or unauthorized inputs.
7. Ensure secret values are never copied into manifests; record credential references/policy identifiers only if required.

Acceptance criteria:
- Changing any included task, rule, convention, project, or authorized reference input changes the snapshot identity.
- Reordering manifest entries does not change identity if canonical ordering is defined.
- Unselected files do not silently enter the task context.
- Tests cover changed rules, changed task definitions, missing files, tampering, and deterministic identity.
- The returned snapshot identity can be independently recomputed from the stored manifest.

### WP-03 — Return contract and cockpit-side acceptance

**Priority:** P0

**Goal:** Treat Shadow output as an untrusted proposal until the cockpit validates and the user accepts it.

Tasks:
1. Version the return schema (current prototype name: `shadow-return-v1`).
2. Define required identity fields: schema version, task ID, run ID, snapshot ID.
3. Standardize outcome states: `completed`, `partial`, `blocked`, `failed`.
4. Define typed structures for findings, assumptions, limitations, open questions, evidence references, tests, metrics, artifacts, and proposed project updates.
5. Validate schema and identity at the acceptance boundary, even if the provider adapter already normalized the response.
6. Recompute/verify the complete input manifest and stale-write guard before applying proposed updates.
7. Keep preview and explicit acceptance separate; no implicit writes on task completion.
8. Record acceptance/rejection decisions and the exact source run/snapshot.
9. Document that local multi-file writes are not transactional unless a transaction mechanism is actually implemented.

Acceptance criteria:
- Wrong task/run/snapshot/schema identity is rejected.
- A result from an outdated snapshot cannot overwrite newer workspace state.
- A malformed or incomplete return is rejected without partial application.
- Preview is side-effect free.
- Tests exercise replayed results, cross-task results, stale snapshots, malformed updates, and acceptance audit records.

### WP-04 — Runtime adapter contract

**Goal:** Keep provider-specific execution behind a small, explicit interface.

Tasks:
1. Specify provider-neutral build, execute, and normalize responsibilities.
2. Keep request construction deterministic and side-effect free.
3. Keep network execution explicit and observable.
4. Normalize provider response status, structured output, usage telemetry, and provider identifiers.
5. Make missing telemetry null/unknown rather than inferred.
6. Align implementation and documentation for cache-write TTL details and diagnostics.
7. Define timeout, cancellation, provider error, incomplete response, and rate-limit behavior; do not add automatic retries until their semantics are specified.
8. Keep tools, filesystem, shell, browser, and network access disabled in the initial adapter.
9. Document provider retention/storage semantics without overclaiming.

Acceptance criteria:
- Adapter contract tests cover request construction, normalization, invalid output, non-completed provider status, timeout/error, and telemetry extraction.
- Provider-specific fields do not leak into the core return contract except through explicitly namespaced metadata.
- Documentation matches the code and tests.
- No live API request occurs during build/plan/dry-run paths.

### WP-05 — Prompt-cache experiment

**Goal:** Measure provider-reported cache behavior without confusing it with architecture quality.

Current arms:
- **K0:** stable and dynamic content mixed in one user message; provider-default cache behavior.
- **K1:** stable developer message plus dynamic user message; implicit cache mode and a stable arm-specific key.
- **K2:** same split layout with explicit stable-prefix breakpoint and a stable arm-specific key.
- **K3:** same as K2, but a different key per run to study key fragmentation.
- **K4:** K2-style request with a changed stable-prefix version and the K2 key. The current default changes the suffix of the stable prefix, so partial reuse of the unchanged leading prefix is possible and expected to be interpreted as such. It is not a model/tool-schema-change experiment.

Tasks:
1. Preserve the exact rendered request body for every run.
2. Record model, response ID, run ID, cache key/mode, breakpoint, stable/dynamic hashes, timestamps, and request interval.
3. Record input, cached, cache-write, TTL-specific write, output, total tokens, latency, and provider diagnostics when available.
4. Track missing telemetry separately; compute hit ratios only on explicitly defined complete samples.
5. Make experiment output append-only or uniquely run-scoped; never silently delete a previous run's raw records.
6. Separate arm-level comparisons from causal claims. K0 vs K1 changes more than one factor; document the confounding. K1 vs K2 primarily examines cache mode/breakpoint under the chosen layout, while key choices must remain explicit.
7. Include controlled repeat intervals inside and beyond the configured cache TTL.
8. Validate the selected model's cache eligibility and actual input token counts; byte length is not token count.
9. Keep cost uncomputed unless a dated, model-specific price schedule and relevant billing fields are supplied.
10. Treat latency as secondary evidence, not as a cache-hit detector.
11. Add a separate real-task replay experiment for task quality; the tiny JSON acknowledgement in the cache harness measures cache mechanics only.
12. Record organization/region only when the provider makes that information available and it can be collected appropriately.

Acceptance criteria:
- Dry-run produces all requests without network calls.
- Live execution is explicit, auditable, and opt-in.
- A failed or incomplete request remains visible in the run record.
- Summary reports sample counts, missing telemetry, absolute cached tokens, hit ratio denominator, write tokens, and latency distribution/mean as appropriate.
- A second run cannot overwrite the first run's raw evidence.
- No cache-hit, cost-saving, or quality claim is made without provider usage evidence and reproducible analysis.

### WP-06 — Execution isolation and security boundary

**Goal:** State and test what is isolated, rather than treating a fresh process as proof of secure isolation.

Isolation dimensions:
1. Context/transcript isolation.
2. Tool-session isolation.
3. Filesystem read/write isolation.
4. Network egress isolation.
5. Credential and secret isolation.
6. Process/container/VM isolation.
7. Provider-side session, storage, and retention behavior.
8. Cross-run artifact and cache-key separation.

Tasks:
- Build a threat model and trust-boundary diagram.
- Define least-privilege input/output mounts and write permissions.
- Define network allow/deny policy.
- Define credential scoping and secret-handling rules.
- Define cleanup and artifact retention behavior.
- Add negative tests that attempt unauthorized file, network, and credential access in the eventual sandbox implementation.
- Keep current subprocess demo explicitly labeled as lifecycle isolation only, not a security boundary.

Acceptance criteria:
- Each isolation dimension is labeled implemented, tested, not implemented, or provider-dependent.
- Negative tests demonstrate denied operations in the chosen production isolation mechanism.
- No production security claim relies solely on subprocess creation or `store=false`.

### WP-07 — Architecture-level comparative experiment

**Goal:** Test whether the proposed architecture provides measurable advantages over plausible alternatives.

Comparison arms:
- **A — Long-lived Agent:** one persistent execution context across a controlled task sequence.
- **B — Parent Agent + sub-agent:** conventional hierarchical delegation with a persistent parent context.
- **C — Cockpit + project files + fresh Shadow:** non-Agent structured workspace and fresh task-scoped execution contexts.

Controls:
- Same model/version where feasible.
- Same task sequence, project inputs, task difficulty, acceptance criteria, and tool permissions.
- Equivalent information availability; do not handicap a baseline by withholding necessary project facts.
- Repeated runs and predeclared scoring rubric.
- Record model/provider changes and any unavoidable differences.

Measures:
- Task success and output quality.
- Constraint adherence and regression rate.
- Error propagation across tasks.
- Recovery after user correction.
- Context growth and irrelevant-context burden.
- Input/output/cached tokens, latency, and total cost.
- Handoff/manifest preparation overhead.
- User review effort and accepted/rejected proposal rate.
- Reproducibility and audit completeness.

Tasks:
1. Define a benchmark project with sequential tasks and controlled changes.
2. Include injected errors and user corrections to test whether stale mistakes propagate.
3. Pre-register hypotheses, scoring rubric, exclusions, and stopping conditions.
4. Run blinded or independently scored output review where practical.
5. Report distributions and failure cases, not only averages or selected successful examples.
6. Distinguish architecture effects from provider caching and prompt-layout effects.

Acceptance criteria:
- Benchmark tasks and scoring rubric are published.
- All arms receive equivalent task-relevant information.
- Raw run metadata and result artifacts are retained.
- Results include negative findings and limitations.
- The architecture is not declared superior unless measured outcomes support that conclusion.

### WP-08 — Independent review and public release

**Goal:** Make the prototype independently inspectable and falsifiable.

Tasks:
1. Consolidate architecture, runtime, manifest, return schema, experiment, and threat-model documentation.
2. Publish exact reproduction commands and environment requirements.
3. Publish CI results tied to commit SHAs.
4. Publish live experiment data with sensitive values removed.
5. Add known limitations and non-claims.
6. Conduct an internal consistency audit across docs, code, schemas, and tests.
7. Invite external reviewers to challenge novelty, prior art, experimental design, and implementation assumptions.
8. Keep the PR in Draft until the agreed acceptance gates are met; do not merge merely because CI passes.

Acceptance criteria:
- A new reviewer can reproduce the mock lifecycle and dry-run cache plan from repository instructions.
- A reviewer can distinguish implemented behavior from hypotheses and live evidence.
- No unverified performance, novelty, security, or cache-hit claim appears in public materials.
- Open architectural decisions are visible and traceable.

## 4. Dependency and execution order

Recommended dependency order:

1. WP-01 terminology and architecture boundary.
2. WP-02 complete input manifest and snapshot identity.
3. WP-03 return validation and acceptance boundary.
4. WP-04 provider-neutral runtime contract and implementation alignment.
5. WP-05 cache experiment hardening and controlled live measurement.
6. WP-06 isolation threat model and staged enforcement.
7. WP-07 comparative architecture experiment.
8. WP-08 independent review and release.

WP-05 and WP-06 can proceed in parallel after the core contracts are stable. WP-07 should not begin until task inputs, return schemas, and measurement definitions are stable enough to compare arms fairly.

## 5. Explicitly deferred decisions

The following are intentionally not decided by this plan:

- Whether dispatch is manual, event-driven, queue-based, or handled by a dedicated scheduler.
- Whether a production Runtime is a service, local process manager, container orchestrator, or provider-native execution facility.
- Whether Shadow tasks may spawn further Shadows.
- Whether tasks may run concurrently and how project-file conflicts are resolved.
- Retry, resume, cancellation, and compensation semantics.
- Which tools, if any, a future Shadow may receive and how permissions are granted.
- Whether any persistent Agent role is ever justified. Such a proposal must be evaluated as a separate architecture variant, not assumed.

These decisions require explicit requirements and experiments; they must not be smuggled into the cockpit definition.

## 6. Risk register

| Risk | Consequence | Mitigation |
|---|---|---|
| Incomplete snapshot inputs | Results cannot be reproduced or safely accepted | Complete manifest and identity validation |
| Untrusted Shadow output | Invalid or stale updates corrupt project state | Validate at acceptance boundary; explicit approval |
| Cache experiment confounding | Incorrect causal interpretation | One-factor controls, raw request capture, cautious claims |
| Missing provider telemetry | Biased cache metrics | Missingness-aware summaries and null handling |
| Subprocess mistaken for sandbox | False security assurance | Threat model and enforced isolation tests |
| Baseline unfairness | Invalid architecture comparison | Equivalent information and predeclared protocol |
| Premature orchestration design | Architecture drifts back toward conventional Agent hierarchy | Keep dispatch and scheduling open |
| Documentation drift | Reviewers cannot identify actual behavior | Evidence labels and doc/code consistency checks |

## 7. Release gates

**Gate A — Contract integrity**
- WP-01 through WP-04 acceptance criteria pass.
- Manifest, return schema, and acceptance behavior are covered by tests.
- Documentation and code are consistent.

**Gate B — Runtime and cache evidence**
- Dry-run and live execution paths are clearly separated.
- Cache harness preserves raw records and handles missing telemetry correctly.
- Live cache behavior is reported only from provider-reported evidence.
- Security limitations remain explicit.

**Gate C — Architecture evidence**
- A/B/C comparison is reproducible.
- Scoring and controls are predeclared.
- Negative results and costs are reported.

**Gate D — Public review**
- Reproduction instructions work from a clean checkout.
- CI evidence is tied to the exact reviewed commit.
- Independent review feedback is addressed or explicitly left open.

Passing a gate does not automatically authorize merging or changing the architecture. Those remain explicit project decisions.

## 8. Immediate next implementation batch

The first code batch should focus on contract correctness, not new infrastructure:

1. Add the complete task input manifest and deterministic snapshot identity.
2. Enforce task/run/snapshot/schema identity at cockpit acceptance.
3. Add tests for rule-file and task-definition changes, not only project-state changes.
4. Make cache harness records run-scoped/append-only and fix missing-telemetry aggregation.
5. Correct stale K4 and harness-status descriptions across documentation.
6. Add this plan to the README and link it from PR #1.

After this batch, rerun the full test matrix and report the exact commit and CI run. Do not run billable live API experiments without explicit authorization.
