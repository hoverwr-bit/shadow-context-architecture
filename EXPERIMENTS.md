# Experiments: Evaluating Shadow Context Architecture

- Status: Proposed protocol; no empirical results claimed
- Version: 0.2
- Related documents: [RFC.md](./RFC.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [CACHE_EXPERIMENT.md](./CACHE_EXPERIMENT.md)

## 1. Purpose

Evaluate whether a structured cockpit backed by versioned project files, combined with fresh task-scoped shadow execution, improves focus stability and context isolation without unacceptable cache, token, latency, or handoff costs.

The experiment must allow negative results. It must not assume the proposed architecture wins.

## 2. Research questions

- RQ1: Does moving project continuity into explicit project files reduce active cockpit-context growth?
- RQ2: Does task focus derived from a pinned project snapshot reduce late-sequence drift and constraint misses?
- RQ3: Does each fresh shadow avoid inheriting previous shadow execution history?
- RQ4: Are errors easier to localize when task inputs, outputs, and project revisions are separately recorded?
- RQ5: Can stable prompt-prefix design preserve cache reuse across fresh shadows?
- RQ6: What are the total token, cache, latency, tool, and handoff costs?
- RQ7: How sensitive is the architecture to stale, contradictory, or incomplete project files?

## 3. Experimental conditions

### A — Long-running agent baseline

A conventional persistent agent performs a sequence of tasks in one accumulating execution conversation. Record normal context handling, compaction, and tool-trace behavior.

### B — Parent-agent plus sub-agent baseline

A competent conventional multi-agent/sub-agent setup uses a persistent parent agent and fresh or isolated workers as supported by the platform. This tests whether the proposal adds value beyond existing sub-agent patterns. Record what the parent agent does and what context it retains.

### C — Cockpit + project files + fresh shadow runtime

A non-agent cockpit holds structured communication and references. Versioned project files define current project state. A separate dispatch mechanism, which may be manual during the pilot, starts a fresh shadow for each task using a pinned task snapshot. The cockpit does not reason as a persistent agent, plan, or coordinate tool execution.

Condition C is the proposed architecture. Do not quietly implement it as a parent Agent delegating to child Agents.

## 4. Controls

Hold constant where possible: model and inference settings; task sequence and difficulty; initial project facts and source materials; tool set and permissions; snapshot content and evidence quality; scoring rubric and evaluator instructions.

Record runtime differences, context policies, memory behavior, tool-session persistence, prompt-cache configuration, and token accounting. Randomize condition order where practical. Use repeated trials.

## 5. Workload design

Use a multi-task project workload with known ground truth. Include:
1. durable constraints introduced early and needed later;
2. decisions that later tasks must respect;
3. irrelevant tool output and retrieval noise;
4. misleading but plausible intermediate evidence;
5. project-state updates and superseded facts;
6. user corrections that must propagate;
7. legitimate cross-task artifact reuse by explicit reference;
8. narrow and broad task boundaries;
9. deliberately stale or contradictory project-file conditions;
10. a task requiring evidence-backed changes to project state.

Publish fixtures and scoring criteria before evaluating outputs.

## 6. Metrics

| Metric | Operational definition | Reporting |
|---|---|---|
| Cockpit active-context growth | Tokens in active cockpit context over task index | Per-task curve |
| Project-state footprint | Size and structure of authoritative active project files | Version-by-version |
| Task focus | Blinded score against task objective and acceptance criteria | Per-task and late-sequence |
| Constraint adherence | Applicable critical constraints satisfied | Pass rate and failures |
| Task quality | Correctness and completeness against ground truth | Distribution |
| Drift | Change in objective deviation over sequence position | Per-task curve |
| Correction propagation | Later tasks correctly apply explicit user corrections | Pass rate |
| Error localization | Reviewer identifies source task/revision of injected error | Accuracy and time |
| Shadow isolation | Prior shadow marker/history inaccessible to later shadow | Pass/fail by channel |
| Prompt cache | Cached input tokens / eligible input tokens, where exposed | Per-task and aggregate |
| Stable-prefix reuse | Common prefix length and actual cache-hit evidence | Per-task |
| Handoff overhead | Snapshot preparation and return-package tokens/time | Per-task and total |
| End-to-end cost | Uncached + cached model tokens, tools, latency, orchestration | Per-task and total |

Do not use cache hit rate alone as a success metric. Report actual cached token counts and cost because providers may define cache eligibility and billing differently.

## 7. Prompt-cache experiment

Run a controlled sub-experiment with the same model/provider/runtime where possible:
- C1: stable system/project rules first, dynamic state and task content last;
- C2: same semantic content but dynamic sections interleaved or reordered;
- C3: stable project prefix with state snapshots pinned by revision, changing only the task suffix;
- C4: state revision changes between tasks, measuring how much prefix remains reusable.

Record exact request prefixes, eligible input tokens, cached input tokens, cache creation/read cost, latency, model, routing if available, and time between requests. Repeat within and beyond documented cache retention windows.

A fresh shadow context does not imply a cache miss. Identical prompts do not guarantee a hit. If the provider does not expose cache telemetry, mark the metric unavailable rather than infer it from latency. For OpenAI-specific breakpoint, routing-key, minimum-prefix, and telemetry requirements, see [CACHE_EXPERIMENT.md](./CACHE_EXPERIMENT.md).

## 8. Isolation tests

1. Put a unique harmless marker only in shadow 1's conversation context.
2. Start shadow 2 with no marker and no access to shadow 1's transcript.
3. Test whether shadow 2 can access the marker.
4. Repeat for persistent memory, tool sessions, temporary files, shared workspaces, and external services.
5. Record each channel as isolated, shared, or unknown.

A model's self-report is not proof. Verify using runtime configuration and observable access controls. Never use secrets as markers.

## 9. Project-file integrity tests

Inject controlled cases: stale state file; conflicting decision revisions; missing provenance; unaccepted proposal presented as fact; accepted correction not reflected in current state.

Measure whether the task package detects or propagates these defects. This tests the architecture's dependency on project-file quality rather than assuming externalization makes facts correct.

## 10. Error localization protocol

Inject errors at distinguishable points: project source, snapshot construction, shadow reasoning, return package, and project-file update. Give reviewers relevant artifacts without revealing the injected point. Score attribution accuracy and time-to-localize.

## 11. Analysis plan

- Pre-register workload, hypotheses, exclusions, and scoring.
- Use paired task sequences where possible.
- Report early, middle, and late task performance.
- Separate cockpit context, project-file footprint, shadow context, and total system cost.
- Report cache hits only when provider telemetry supports them.
- Show distributions and uncertainty, not just averages.
- Include failed, blocked, and incomplete runs.
- Do not claim causality where runtime or context quality differs materially.

## 12. Minimum results table

| Metric | A: Long-running | B: Parent + sub-agent | C: Cockpit + shadow |
|---|---:|---:|---:|
| Task acceptance rate | TBD | TBD | TBD |
| Critical constraint pass rate | TBD | TBD | TBD |
| Late-sequence focus score | TBD | TBD | TBD |
| Cockpit/parent context growth | TBD | TBD | TBD |
| Project-state integrity | N/A or measured | N/A or measured | TBD |
| Shadow isolation | N/A | TBD | TBD |
| Cached input tokens | TBD | TBD | TBD |
| Handoff overhead | TBD | TBD | TBD |
| End-to-end cost | TBD | TBD | TBD |
| Error localization accuracy | TBD | TBD | TBD |

Do not fill TBD values with estimates.

## 13. Threats to validity

Model nondeterminism; unequal project-state curation; hidden runtime memory or shared tool state; provider cache opacity and routing effects; task fixtures favoring one workflow; evaluator bias; inaccurate token accounting; task granularity effects; poor project-file quality; manual dispatch during pilot differing from automated runtime.

## 14. Pilot proposal

Start with one documented 12–20 task project sequence and at least three exploratory runs per condition. Use one fixed model/runtime where possible, a published constraint checklist, and blinded review for a subset. This is a feasibility pilot, not proof of general superiority.

## 15. Current status

No empirical results are claimed. This protocol is a proposal until a pilot is executed and evidence is published.
