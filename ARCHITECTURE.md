# Architecture: Persistent Main Conversation and Ephemeral Shadows

- Status: Design note
- Version: 0.1
- Related specification: [RFC.md](./RFC.md)

## 1. Design invariant

The main conversation is persistent and owns continuity. A shadow is created fresh for one bounded task, executes within its own temporary context, returns a structured result, and ends.

The architecture is not a pair of peer agents with equal memory. It is a persistent context manager delegating isolated execution.

## 2. Logical components

### 2.1 Main conversation / orchestrator

Responsibilities:
- maintain user-facing dialogue and relevant continuity;
- maintain structured context such as goals, decisions, constraints, current state, and unresolved questions;
- define a bounded task and its acceptance criteria;
- assemble the task context package;
- select the references and permissions available to the shadow;
- receive and review the return package;
- expose the result to the user so incorrect judgments can be identified and corrected;
- decide what conclusions should be retained for future tasks.

The main conversation does not need to ingest the shadow's complete tool trace, intermediate reasoning, or raw logs.

### 2.2 Shadow execution instance

Responsibilities:
- start as a new task-scoped execution context;
- consume the task context package;
- perform analysis, retrieval, tool calls, code execution, and tests as required;
- distinguish observed evidence from assumptions and recommendations;
- return the requested outcome with sufficient evidence and caveats;
- terminate after the task.

A shadow must not rely on another shadow's conversation history. If it needs an earlier artifact or decision, that information must be supplied by the main conversation or retrieved from an explicitly authorized source.

### 2.3 External sources and artifacts

Repositories, specifications, issue trackers, test reports, and other authorized systems may hold durable project facts and outputs. They are sources the main conversation can reference when preparing a task package. Their existence does not turn a shadow into a stateful agent.

## 3. Data flow

```text
             Persistent continuity boundary
   USER <------> MAIN CONVERSATION / ORCHESTRATOR
                         |
                         | 1. task + selected context
                         v
                 [Fresh shadow instance]
                         |
             2. task-local work and tool use
                         |
                         v
                 [Return package]
                         |
                         | 3. result only, not full trace
                         v
   USER <------> MAIN CONVERSATION / ORCHESTRATOR
                         |
              4. review, correction, retention
                         |
                         v
                Updated structured context

        Next task => another fresh shadow instance
```

The boundary is logical and must be enforced by the runtime. Merely naming a second conversation a “shadow” does not establish isolation.

## 4. Task context package

A practical package can use this conceptual shape:

```yaml
task_id: "unique-task-reference"
objective: "One bounded outcome"
acceptance_criteria:
  - "Observable completion condition"
relevant_context:
  current_state: "Only the state needed for this task"
  accepted_decisions: []
constraints:
  must: []
  must_not: []
references:
  - "Repository path, document, or source"
tool_permissions:
  allowed: []
  denied: []
uncertainties:
  - "Known unknowns; do not silently assume"
output_contract:
  format: "structured result"
  include_evidence: true
```

This is illustrative, not a mandatory serialization format. The package should be minimal enough to avoid unnecessary context transfer but complete enough to preserve task-critical meaning.

### Context selection questions

Before dispatch, the main conversation should be able to answer:
- What exactly is the requested outcome?
- Which prior decisions materially constrain this task?
- Which facts are current, and how are they supported?
- Which references can the shadow inspect?
- What is explicitly unknown?
- What would count as completion or failure?

## 5. Return package

A practical return shape:

```yaml
task_id: "unique-task-reference"
status: "completed | partial | blocked | failed"
result: "Concise outcome"
findings:
  - statement: "Evidence-backed finding"
    evidence: ["source or artifact reference"]
recommendations:
  - "Recommendation, clearly not a confirmed fact"
assumptions: []
open_questions: []
artifacts: []
context_update_candidates:
  - "Potentially reusable information for main conversation review"
```

The shadow should return enough evidence to make its result inspectable. It should not transfer its entire working transcript by default. The main conversation remains responsible for deciding what becomes retained context.

## 6. Lifecycle and state transitions

| State | Meaning | Next state |
|---|---|---|
| Prepared | Task and relevant context assembled | Created |
| Created | Fresh shadow runtime initialized | Executing |
| Executing | Task-local work is underway | Returning / Failed / Cancelled |
| Returning | Structured result is emitted | Closed |
| Closed | Shadow context is ended | None |
| Failed / Cancelled | Run did not complete normally | Closed after status is recorded |

The lifecycle is per task. A later task starts at Prepared and receives a new execution instance.

## 7. Isolation requirements

A runtime claiming to implement this architecture should verify:

1. **Conversation isolation:** a new shadow receives no previous shadow transcript.
2. **Memory isolation:** no shadow-specific persistent memory is silently reused across tasks.
3. **Tool-session isolation:** tool sessions and temporary execution state are task-scoped or explicitly documented.
4. **Permission scoping:** access is limited to the task's declared tools, files, credentials, and actions.
5. **Artifact continuity by reference:** prior outputs are reused only through explicit references supplied or authorized for the current task.
6. **Return boundary:** only the defined return package is sent into the main conversation by default.
7. **Termination semantics:** task completion ends the shadow's active context; any retained artifact or audit log is separately identified.

These requirements distinguish genuine lifecycle isolation from simply opening multiple tabs or threads.

## 8. Failure handling

- **Insufficient package:** shadow returns a clarification request or blocked status instead of inventing missing context.
- **Conflicting context:** shadow identifies the conflict and cites the competing sources.
- **Tool failure:** shadow reports the failed operation, impact, and whether the task is partial.
- **Acceptance criteria not met:** shadow returns partial/failed status and identifies unmet criteria.
- **Incorrect conclusion:** main conversation and user can challenge the result; corrected information is retained by the main conversation as appropriate.
- **Runtime cannot guarantee isolation:** implementation must disclose the limitation and must not claim full statelessness.

## 9. Architecture decisions versus implementation choices

The following are defining properties:
- persistent main conversation;
- fresh shadow per bounded task;
- no cross-task shadow execution history;
- task-specific context supplied by the main conversation;
- bounded return to the main conversation;
- shadow lifecycle ends after its task.

The following remain implementation choices:
- JSON, YAML, or another package format;
- one model or different models for main and shadow;
- synchronous or asynchronous dispatch;
- exact tool/runtime technology;
- whether evidence artifacts are stored in Git, another system, or both;
- whether a human explicitly approves every context update.

Implementation choices must not undermine the defining properties.

## 10. Open design questions

- How should the main conversation detect stale or contradictory structured context?
- Should task packages carry provenance and timestamps for each important fact?
- Which tasks are too broad to qualify as one bounded shadow run?
- What minimum audit metadata should survive shadow termination?
- How can runtime isolation be tested rather than merely asserted?

See [EXPERIMENTS.md](./EXPERIMENTS.md) for a proposed validation plan.
