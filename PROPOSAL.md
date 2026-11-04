# Why Persistent Agent Context May Become a Liability

## A proposal for a non-Agent Cockpit and task-scoped Shadow execution

### Abstract

Long-running agent workflows often rely on a persistent conversation or coordinating agent to carry project context from one task to the next. This is convenient, but it creates a difficult systems question: as execution traces, intermediate assumptions, tool outputs, corrections, and stale information accumulate, does the active context remain focused on the current project state and task?

This proposal explores a different boundary. Instead of making the primary workspace another persistent agent, it treats the Cockpit as a structured, persistent workspace backed by project files. Each task is executed in a fresh, bounded Shadow context that receives an explicit task package and returns a structured proposal. The user reviews and accepts changes before they become durable project state.

This is an architectural hypothesis, not a demonstrated performance result. The current repository contains an experimental lifecycle demo, a provider adapter, and a prompt-cache experiment harness. It does not yet establish that this architecture outperforms long-lived agents, guarantees cache hits, or provides production-grade isolation.

## 1. The problem: context accumulation is not the same as memory

A long-running agent can retain useful information, but its context may also contain:

- Tool-call traces and intermediate outputs that are no longer relevant.
- Earlier assumptions that have since been corrected.
- Partial plans and abandoned approaches.
- Repeated explanations and summaries.
- Conflicting versions of project state.
- Historical details that compete with the current task for attention.

The issue is not simply that the context becomes large. It is that the active execution context must continually distinguish durable project facts from transient execution history.

A larger context window may postpone capacity pressure. It does not, by itself, define which information is authoritative, which information is stale, or which information should influence the next task.

The hypothesis here is that project focus should be established structurally, from an explicit project state and task package, rather than reconstructed from an ever-growing conversation history.

## 2. Why a larger context window may not be enough

More context capacity can be useful. It is not a complete context-governance strategy.

A system still needs answers to questions such as:

1. Which project files represent the current accepted state?
2. Which task-specific references are authorized inputs?
3. How are corrections propagated and old assumptions retired?
4. How can a task be reproduced from a known set of inputs?
5. How can an incorrect result be prevented from silently changing durable state?

These are lifecycle and state-management questions, not just token-budget questions.

## 3. The alternative: a non-Agent Cockpit

The proposed architecture separates persistent project state from transient execution.

### Cockpit

The Cockpit is a persistent, structured, user-facing workspace. It is not an Agent, planner, parent Agent, or orchestrator. Its role is to present project state, define or select tasks, display execution results, and provide an explicit review and acceptance boundary.

### Project files

Project files are the durable source of accepted project state: decisions, constraints, specifications, records, and accepted outputs. They should be inspectable and versionable independently of a conversation transcript.

### Shadow

A Shadow is a fresh, task-scoped execution context. It receives only the task package and authorized inputs for that run. It returns a bounded, structured result, including findings, assumptions, limitations, open questions, and proposed project updates.

A Shadow does not inherit another Shadow's conversation transcript or tool trace.

### Runtime

The Runtime creates and contains an execution run. The current prototype uses a separate local subprocess for the mock lifecycle. That is a demonstration of process separation, not a security sandbox. Production dispatch, scheduling, concurrency, retries, and isolation mechanisms remain open design questions.

## 4. The lifecycle and acceptance boundary

A task follows this conceptual lifecycle:

1. The user selects or defines a task in the Cockpit.
2. The system assembles a task package from the task definition, selected project state, stable rules, conventions, and authorized references.
3. A fresh Shadow receives that package.
4. The Shadow returns a bounded result tied to the task and snapshot identity.
5. The Cockpit presents the result for inspection.
6. The user reviews and explicitly accepts or rejects proposed project updates.
7. Accepted updates become part of the durable project state and can be used to prepare a later task.

The important boundary is that an execution result is not automatically project truth. It remains a proposal until it passes validation and explicit acceptance.

The current implementation does not yet fully enforce all of the intended contract requirements. In particular, complete task-input identity and independent Cockpit-side validation are still open work packages.

## 5. Why not simply use a parent Agent and sub-agents?

A parent Agent with short-lived sub-agents is a plausible alternative. It may improve task decomposition and parallel execution.

However, it preserves a persistent coordinating context. That parent still has to decide what to remember, what to discard, which sub-agent results are authoritative, and how corrections update its working state.

The proposed Cockpit takes a different position: durable project state lives outside the execution context, in explicit project artifacts. The Cockpit itself does not need to reason as an Agent. A task-specific Shadow can be discarded after returning its bounded result.

This is not a claim that parent-agent systems cannot work. It is a distinction worth testing: does a non-Agent workspace with explicit state and acceptance boundaries reduce cross-task error propagation or review burden under controlled conditions?

## 6. The prompt-cache question

Fresh execution contexts do not inherently imply prompt-cache misses. Cache reuse depends on provider-specific request matching and routing behavior, not on preserving one conversational agent instance.

The proposed prompt layout separates:

- A stable prefix: shared rules, conventions, and stable output contract.
- A dynamic suffix: current task, project snapshot, and task-specific references.

A stable cache key and explicit cache breakpoint may support reuse when the provider's eligibility and routing conditions are met. But request construction is not evidence of a cache hit. Only provider-reported usage telemetry can establish whether input tokens were actually cached.

The repository includes a K0–K4 cache experiment harness with a network-free planning path and an explicit opt-in execution path. No live cache experiment has yet been run. Cache hit rates, latency improvements, and cost savings are therefore unproven.

## 7. What has been implemented

The prototype currently includes:

- A standard-library-based mock lifecycle for workspace initialization, task preparation, execution, inspection, and explicit acceptance.
- A bounded `shadow-return-v1` result contract.
- A fresh subprocess for each mock Shadow run.
- A stale project-file guard for proposed updates.
- An experimental OpenAI Responses API request adapter with side-effect-free request construction and an explicit network execution method.
- A cache experiment harness that builds K0–K4 requests, records raw telemetry when executed, and supports a dry-run mode without network calls.
- Automated tests across Python 3.10, 3.11, 3.12, and 3.13.

These are prototype capabilities. A passing test suite validates only the behavior covered by those tests on the specific commit being tested.

## 8. What still needs to be proven

Several important properties remain unproven or incomplete:

- **Complete input identity:** the snapshot identity must cover every task input that can affect execution, including task definitions, stable rules, conventions, authorized references, and relevant runtime configuration.
- **Acceptance integrity:** the Cockpit must independently validate schema, task, run, and snapshot identity, and revalidate the complete input manifest before applying updates.
- **Cache behavior:** real provider runs must establish whether stable prefixes are reused across fresh Shadow runs, including missing telemetry and cache-write behavior.
- **Security isolation:** a subprocess running under the same operating-system user is not a security boundary. Filesystem, network, credentials, and process isolation require a threat model and enforced controls.
- **Architecture effectiveness:** the proposed workflow must be compared against credible alternatives using equivalent task information and permissions.
- **Operational costs:** manifest construction, handoff, review, retries, and project-state maintenance may introduce overhead that must be measured.

## 9. A comparative experiment

A useful evaluation would compare at least three arms:

- **A — Long-lived Agent:** one persistent execution context across a controlled sequence of tasks.
- **B — Parent Agent plus sub-agents:** a persistent coordinator delegates bounded subtasks.
- **C — Cockpit plus project files plus fresh Shadow:** a non-Agent workspace prepares task-scoped execution contexts and applies only accepted updates.

All arms should receive equivalent task-relevant information, tool permissions, model versions where feasible, and acceptance criteria.

Measurements should include:

- Task success and output quality.
- Constraint adherence and regression rate.
- Propagation of injected errors across later tasks.
- Recovery after user correction.
- Context growth and irrelevant-context burden.
- Input, output, and cached tokens; latency; and total cost.
- Handoff and manifest preparation overhead.
- User review effort and proposal acceptance/rejection rates.
- Reproducibility and audit completeness.

The protocol should predeclare tasks, scoring criteria, exclusions, and stopping conditions. It should retain raw run metadata and report negative results as well as positive ones.

The architecture should not be declared superior unless measured outcomes support that conclusion.

## 10. The core architectural principle

The central proposal is simple:

**Keep durable project state in explicit project artifacts. Keep execution context task-scoped. Keep changes reviewable until explicitly accepted.**

This does not eliminate the need for context, reasoning, or coordination. It changes where continuity lives and how execution results become durable state.

The Cockpit is the persistent workspace, not another persistent Agent.

## Discussion

This repository is an invitation to inspect and challenge the design, not a claim of completed research. Feedback is especially valuable on the completeness of the task manifest, the acceptance boundary, the security model, the fairness of the A/B/C experiment, and relevant prior art.

Issues and pull requests are welcome. Please distinguish implementation defects from architectural disagreements and from hypotheses that require empirical testing.
