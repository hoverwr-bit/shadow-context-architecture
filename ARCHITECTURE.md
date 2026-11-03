# Architecture: Structured Cockpit + Ephemeral Task Runtime

- Status: Design note
- Version: 0.2
- Related specification: [RFC.md](./RFC.md)

## 1. Architectural thesis

The system does not use a persistent main Agent to coordinate long-running work.

It separates four concerns:
1. **Cockpit:** persistent user-facing workspace for structured communication, project focus, review, and correction.
2. **Project files:** versioned source of truth for project goals, constraints, decisions, progress, and evidence.
3. **Dispatch/runtime mechanism:** starts task execution and enforces boundaries; implementation responsibility remains open.
4. **Shadow:** fresh, disposable execution context for one bounded task.

The cockpit is not a planner, orchestrator, or tool-running agent. The shadow does not carry continuity between tasks.

## 2. Components and responsibilities

### 2.1 Cockpit / structured workspace

- displays current project focus and structured status;
- records user communication, corrections, confirmations, and open questions;
- links to authoritative project files and task artifacts;
- presents shadow return packages for human review;
- provides an interaction surface for accepting or rejecting proposed project-state changes.

It should not become a duplicate of all project documents or a sink for tool logs. It does not independently decide task plans or act as the persistent execution controller.

### 2.2 Project files

- hold versioned project goals, constraints, decisions, specifications, progress, and evidence;
- identify current versus superseded information;
- preserve provenance and revision identifiers where practical;
- provide task snapshots from known revisions;
- receive accepted updates through normal versioned changes.

Project files, not the chat transcript, are the durable project-state authority.

### 2.3 Dispatch/runtime mechanism (open)

Required capabilities, regardless of implementation:
- accept a bounded task request;
- resolve the required project snapshot and references;
- initialize a fresh shadow context;
- scope tools, credentials, filesystem access, and network permissions;
- collect the structured return package;
- close the task execution context;
- record enough audit metadata to verify lifecycle and isolation.

This mechanism may be user-triggered, host-provided, or implemented as a separate non-conversational service. The architecture does not currently prescribe which. It must not silently be modeled as a persistent main Agent.

### 2.4 Shadow execution instance

- starts with a fresh task-scoped context;
- receives the task package and explicitly authorized project references;
- performs analysis, retrieval, tool calls, code execution, and tests;
- distinguishes observed evidence from assumptions and recommendations;
- returns a bounded result with evidence and proposed changes;
- ends after the task.

It must not inherit a previous shadow's transcript or task-local working context.

## 3. Data flow

    USER <----> COCKPIT
                   |
                   | reads / discusses / proposes updates
                   v
            VERSIONED PROJECT FILES
                   |
                   | pinned task snapshot + references
                   v
           DISPATCH / RUNTIME MECHANISM
                (implementation TBD)
                   |
                   v
           FRESH SHADOW EXECUTION
             | tools / retrieval / tests |
                   |
                   v
            STRUCTURED RETURN PACKAGE
                   |
                   v
           COCKPIT: display and review
                   |
             user acceptance/correction
                   |
                   v
           VERSIONED PROJECT FILES

    Next task -> new shadow context

The diagram intentionally does not show the cockpit calling a sub-agent as an Agent-to-Agent delegation pattern. The task-start mechanism is a separate unresolved component.

## 4. Project-state model

A practical project layout may include:
- PROJECT.md: purpose, scope, authoritative entry point;
- STATE.md: current progress, active milestone, blockers, next verified actions;
- DECISIONS.md: accepted decisions, rationale, date, supersession links;
- CONSTRAINTS.md: durable must/must-not requirements;
- SPEC/: detailed requirements and architecture;
- TASKS/: task definitions, snapshots, and acceptance criteria;
- EVIDENCE/: test reports, measurements, source references, and review records.

This is a suggested organization, not a required repository layout. Avoid copying the entire project into every task prompt. Select relevant files and pin exact revisions.

## 5. Task snapshot contract

Illustrative fields:
- task_id and project_id;
- snapshot revision and exact file revisions;
- one bounded objective;
- observable acceptance criteria;
- relevant decisions and known uncertainties;
- authorized references;
- tool, filesystem, and network permissions;
- output schema and evidence requirements.

The snapshot should be immutable for the duration of the task. If authoritative project state changes mid-run, the task should either continue against its pinned snapshot or be explicitly restarted with a new one.

## 6. Return package contract

Illustrative fields:
- task_id and status: completed, partial, blocked, or failed;
- snapshot revision used;
- concise result;
- evidence-backed findings;
- assumptions, limitations, and open questions;
- artifacts created or changed;
- proposed project-file updates;
- tests performed and results.

The return package is not the full execution transcript. It must be sufficient for review and identify the snapshot it used.

## 7. Context layering and cache-aware ordering

Candidate prompt order:
1. stable system rules and output protocol;
2. stable project conventions and architecture;
3. current versioned project snapshot;
4. task-specific objective, inputs, and acceptance criteria.

Stable layers should be identical where practical if the provider's cache requires exact prefix reuse. Dynamic task content belongs later. A project-state update changes the relevant dynamic section; it should not require rewriting unrelated stable sections.

This is an optimization opportunity, not a guarantee. Prompt caching is provider-specific and may depend on minimum prefix length, retention time, request routing, model, tool definitions, and other factors. Never keep stale project state just to preserve a cache hit.

## 8. Lifecycle and state transitions

| State | Meaning |
|---|---|
| Prepared | Task and immutable snapshot defined |
| Initialized | Fresh execution context created |
| Executing | Shadow performs task-local work |
| Returning | Structured result emitted |
| Closed | Active execution context ended |
| Failed / Cancelled | Failure recorded; context closed |

Each new bounded task must begin with a new execution context. Reusing a previous shadow conversation is outside the defining architecture.

## 9. Isolation and audit requirements

A conforming implementation should test and document:
- conversation history isolation;
- cross-task memory isolation;
- tool-session and credential scope;
- filesystem and temporary-file scope;
- external service state and caches;
- explicit artifact reuse by reference;
- return-package boundary;
- runtime termination semantics.

Do not equate ending a chat transcript with deleting every external artifact or log. Retained audit evidence must be separately identified and access-controlled.

## 10. Failure handling

- Missing required project state: return blocked or clarification-needed, do not silently infer.
- Conflicting project files: report conflict and identify competing revisions.
- Stale snapshot: disclose the snapshot revision; restart only through an explicit new task.
- Tool failure: report impact and partial status.
- Failed acceptance criteria: identify unmet criteria.
- Incorrect shadow judgment: cockpit presents evidence for user challenge; accepted correction updates project files.
- Isolation not guaranteed: disclose unisolated channels; do not claim full statelessness.
- Cache miss: treat as a performance observation, not a correctness failure.

## 11. Defining invariants vs implementation choices

Defining:
- cockpit is not an Agent or orchestrator;
- project files hold durable project state;
- each bounded task uses a fresh shadow context;
- no previous shadow execution history is inherited;
- task execution traces do not automatically enter cockpit context;
- results return through a bounded structured contract;
- accepted project-state changes are versioned.

Open implementation choices:
- task dispatch trigger and component;
- runtime/provider/model;
- synchronous or asynchronous execution;
- package serialization;
- project repository technology;
- cache strategy and provider-specific controls;
- approval policy for project updates.

See [EXPERIMENTS.md](./EXPERIMENTS.md) for validation.
