# RFC: Shadow Context Architecture

- Status: Draft / Experimental Proposal
- Version: 0.2
- Date: 2026-11-04
- Core model: Persistent Structured Cockpit + Ephemeral Task Runtime

## 1. Abstract

Shadow Context Architecture separates project continuity from task execution.

The persistent user-facing main session is a **cockpit/workspace**, not a main agent. Its role is to hold and display structured communication: project goals, constraints, accepted decisions, current progress, open questions, user corrections, and links to project artifacts. It is not the long-running reasoning or tool-execution controller.

Project files are the durable, versioned source of project state. The cockpit is the interaction surface through which the user and system inspect, discuss, correct, and explicitly update that state. Conversation history is not treated as the authoritative project database.

Each bounded task runs in a newly created **shadow execution context**. The shadow receives a task-specific snapshot of relevant project state and authorized references. It may reason, retrieve, call tools, run code, and test inside that temporary context. Its intermediate execution trace does not flow back into the cockpit. It returns a bounded, structured result for inspection and possible incorporation into project files. The task context then ends; the next task starts fresh.

The mechanism that triggers, schedules, or dispatches task runtimes is deliberately implementation-neutral. It may be user-triggered, host-provided, or implemented by a separate runtime mechanism. This RFC does not assume a persistent hidden orchestrator agent.

## 2. Problem statement

Long-running agent workflows commonly mix durable project intent with transient execution material: tool calls, search results, logs, retries, intermediate hypotheses, and stale findings. The system must then recover current focus from a growing conversational context.

This proposal changes the source of continuity. Instead of asking an agent to repeatedly rediscover project focus from conversation history, current focus is represented directly in versioned project artifacts. Execution contexts are temporary and task-scoped.

The central hypothesis:

> Project continuity should live in explicit, inspectable project state; task execution should happen in disposable contexts that do not accumulate one another's traces.

## 3. Core concepts

### Cockpit / structured workspace
A persistent user-facing interaction surface. It records structured communication and exposes project state. It is not an autonomous agent, planner, orchestrator, or execution controller.

Typical information: current project focus; user goals and constraints; confirmed decisions and corrections; progress and open questions; references to authoritative project files and task results.

### Project files / project state
Versioned external artifacts representing authoritative project state: specifications, decisions, architecture, task status, acceptance criteria, test evidence, and other project records. Distinguish current facts from assumptions, proposals, and superseded decisions.

### Shadow execution context
A fresh, temporary execution environment for one bounded task. It receives only the task package and explicitly authorized project references. It does not inherit a previous shadow's conversation or execution history.

Fresh context does not imply all infrastructure state is fresh: filesystem state, caches, credentials, tool sessions, provider memory, and external services must be separately scoped and tested.

### Task snapshot
An immutable, versioned view of project information selected for one task. It records which project revisions and references were used.

### Return package
A bounded result containing status, findings, evidence, artifacts, caveats, and proposed project-state changes. It is not a dump of the shadow's complete transcript.

### Runtime / dispatch mechanism
The mechanism that starts a fresh shadow, supplies its package and permissions, collects the return package, and closes the run. Its implementation and responsibility boundaries remain open. It is not assumed to be a persistent conversational agent.

## 4. Architecture

    USER
      |
      v
    Persistent Cockpit / Workspace
      - structured communication
      - project focus and status
      - decisions / constraints
      - review and correction surface
      - no long-running Agent role
      |
      v
    Versioned Project Files
      - current state, specifications, decisions
      - progress, evidence, task and acceptance records
      |
      | task snapshot + references (dispatch mechanism TBD)
      v
    Fresh Shadow Execution Runtime
      - task-local reasoning, tools, retrieval, code, tests
      - no prior shadow transcript
      |
      v
    Structured Return Package
      |
      v
    Cockpit displays for review; accepted changes update project files.

The cockpit is not the dispatcher. Project files are not an agent memory transcript. The shadow is not a persistent sub-agent. The dispatch/runtime mechanism is a separate unresolved implementation concern.

## 5. Operating cycle

1. User and cockpit identify the current project focus through structured communication.
2. Project files define the current authoritative state.
3. A bounded task is initiated through an implementation-neutral dispatch mechanism.
4. A task snapshot is created from specific project-file revisions and authorized references.
5. A fresh shadow executes without previous shadow conversation history.
6. The shadow returns a structured result with evidence, caveats, and proposed artifact changes.
7. The cockpit presents the result; the user can challenge, correct, or accept it.
8. Accepted changes are written to versioned project files with traceable revisions.
9. The shadow runtime ends. The next task receives a new execution context and a newly prepared snapshot.

## 6. Context and focus principles

### Context-independent focus
Current task focus is derived from explicit project state, not reconstructed from a large accumulated transcript. This aims to make focus an architectural property rather than a continuous context-recovery task.

### Bounded cockpit context
The cockpit retains structured communication and references, not raw execution traces. It should point to project files rather than duplicate every project detail indefinitely. Active context should remain bounded through current-state views, versioned records, and archival of superseded material.

### Ephemeral execution
Each shadow receives task-relevant state and starts without previous shadow execution history. Task-local reasoning, tool traces, retries, and logs remain within the execution boundary unless selected evidence is explicitly returned.

### Correctness is not guaranteed by focus
Project files can be stale, incomplete, contradictory, or wrong. Provenance, versioning, validation, and user correction remain necessary. A focused input can still produce an incorrect result.

## 7. Stable prefixes and prompt caching

Fresh execution contexts do not inherently prevent prompt-cache reuse. Reuse may be possible when repeated requests share an identical prefix and the provider/runtime supports compatible caching.

Candidate input order:
1. stable system and safety rules;
2. stable project conventions and architecture references;
3. current versioned project-state snapshot;
4. task-specific objective, inputs, and acceptance criteria.

Stable content should precede dynamic content where the platform's cache semantics reward exact prefix reuse. Do not distort or omit current project facts merely to preserve a cache hit. Cache behavior depends on provider-specific rules, minimum prefix sizes, retention windows, routing, and request details; it must be measured, not assumed.

## 8. Task and return contracts

A task package should identify task ID and objective; acceptance criteria; project snapshot ID and exact file revisions; relevant decisions and constraints; authorized references and tools; known uncertainties and conflicts; output schema and evidence requirements.

A return package should identify task ID and status; result and evidence-backed findings; assumptions, limitations, and unresolved questions; artifacts created or changed; proposed project-file updates; tests performed and results.

The return package must distinguish facts, interpretations, recommendations, and proposed changes.

## 9. Design invariants and open implementation questions

Defining invariants:
- the cockpit is a structured interaction workspace, not the main agent;
- project files are the durable source of project state;
- each bounded task receives a fresh shadow execution context;
- prior shadow conversation/execution history is not inherited;
- execution traces do not automatically flow into the cockpit;
- results return in a bounded, reviewable structure;
- accepted project-state changes are versioned.

Open questions:
- what component or actor triggers and dispatches each task?
- which runtime guarantees context and tool-session isolation?
- how are project snapshots generated and pinned?
- what is the minimal useful cockpit schema?
- which return fields are mandatory for each task class?
- how are cache keys, stable prefixes, and cache metrics exposed by a provider?
- how should multi-stage tasks be split without recreating a long-lived execution context?

## 10. Risks and failure modes

Stale or incorrect project files can systematically misdirect every new shadow. Over-curated task packages may omit critical context. Cockpit conversation can still grow if it duplicates project records. Hidden runtime state may violate assumed isolation. Excessive task fragmentation can increase handoff overhead. Stable-prefix optimization may be defeated by dynamic content or provider behavior. Cache optimization may conflict with freshness if misapplied. A result-only return can omit important evidence unless the return contract is strong.

## 11. Experimental hypotheses

- H1: cockpit active-context growth is lower and more bounded when project state is externalized and execution traces are excluded.
- H2: task focus and constraint adherence are more stable when each task starts from an explicit project snapshot.
- H3: errors become easier to localize when task inputs, outputs, and project revisions are separately recorded.
- H4: fresh shadows prevent previous shadow transcripts from accumulating in later shadow contexts, if runtime isolation is real.
- H5: stable-prefix organization can preserve some prompt-cache reuse across fresh shadow runs, subject to provider behavior.
- H6: snapshot preparation, initialization, and handoffs may add cost and latency.

These are hypotheses, not empirical findings.

## 12. Prior-art positioning

Fresh contexts, sub-agents, context resets, structured handoffs, and external project artifacts all have prior art. This proposal should not claim those mechanisms individually as inventions.

The candidate distinction is the combined operating model: a non-agent structured cockpit, project files as the continuity/focus substrate, task-scoped disposable execution, explicit no-trace-backflow, and evaluation of focus stability, project-state quality, isolation, and cache/cost trade-offs. Whether this combination is novel or materially advantageous remains unproven.

## 13. Prototype stages

- Stage 0: agree on cockpit/project-state/task/return contracts.
- Stage 1: manually simulate the workflow using project files and independent fresh sessions.
- Stage 2: measure context growth, task quality, isolation, and cache behavior.
- Stage 3: implement a separate dispatch/runtime mechanism.
- Stage 4: invite independent reproduction and critique.

## 14. Review invitation

Reviewers are invited to challenge the separation of cockpit, project state, dispatch mechanism, and ephemeral execution; identify prior art; test whether project-file focus improves task quality; and measure cache, latency, and total-cost effects.

No empirical superiority or runtime guarantee is claimed.

## Change log

- 0.1 — Initial draft incorrectly described a persistent main conversation as an orchestrator.
- 0.2 — Reframed the main session as a non-agent structured cockpit; made project files the durable continuity source; separated dispatch/runtime as an open implementation concern; added focus and prompt-cache hypotheses.
