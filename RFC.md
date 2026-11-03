# RFC: Shadow Context Architecture

- Status: Draft / Experimental Proposal
- Version: 0.1
- Date: 2026-11-04
- Core model: Persistent Conversation Orchestrator + Ephemeral Stateless Execution Agent

## 1. Abstract

Shadow Context Architecture separates persistent conversational continuity from short-lived task execution.

The **main conversation** remains the user-facing, persistent context center. It maintains relevant dialogue, structured conclusions, current goals, constraints, decisions, and project state.

For each bounded task, the main conversation creates a **new shadow agent**. The shadow receives a task-specific package assembled from the main conversation's current structured context and the current discussion relevant to that task. It may analyze, search, retrieve files, call tools, execute code, and test within its own run. Its intermediate execution history is not appended to the main conversation. It returns only the task result and structured conclusions needed by the main conversation, then its execution context ends.

Every subsequent task receives a fresh shadow. No previous shadow's conversation or execution history is inherited.

The proposal seeks to reduce accumulated tool noise, intermediate traces, stale assumptions, and unrelated execution details in long-running agent contexts. It does not claim that the main conversation is immune to context growth or attention dilution. The architecture and its hypotheses require empirical validation.

## 2. Problem

Long-running agent contexts can mix durable user intent and decisions with transient search results, tool calls, logs, retries, intermediate analysis, temporary hypotheses, and failed approaches. As this material accumulates, important constraints may compete with execution noise for attention. The system may repeat work, forget constraints, or drift without a clear failure boundary.

The central hypothesis is that **continuity management and task execution do not need to share one accumulating execution context**.

## 3. Terminology

### Main conversation
The persistent user-facing conversation and context center. It maintains continuity and decides what information is useful to retain: relevant dialogue, structured context, accepted decisions, constraints, current state, user corrections, and selected task conclusions.

### Shadow agent
A newly instantiated, short-lived agent for one bounded task. It receives task-specific context, performs the task, returns a bounded result, and ends. It has no cross-task conversational or execution-history continuity. “Stateless” does not mean it cannot use information supplied for the current task, access authorized project files, or use tools during its run.

### Task context package
The task-specific input assembled by the main conversation, containing the objective and only the relevant context, constraints, references, permissions, and output requirements.

### Return package
The bounded result sent back to the main conversation. It is not a wholesale dump of the shadow's working transcript.

### Structured context
Explicitly represented goals, constraints, decisions, assumptions, references, project state, and open questions maintained by the main conversation.

## 4. Architecture

```text
                         USER
                           |
                           v
              +---------------------------+
              |       MAIN CONVERSATION   |
              |       Persistent          |
              |                           |
              | - ongoing dialogue        |
              | - structured context      |
              | - decisions / constraints |
              | - current state           |
              | - user corrections        |
              +---------------------------+
                           |
                 build task-specific input
                           |
                           v
              +---------------------------+
              |      NEW SHADOW AGENT     |
              |      Ephemeral            |
              |                           |
              | - analyze                 |
              | - retrieve / search       |
              | - use tools               |
              | - execute / test          |
              | - produce result          |
              +---------------------------+
                           |
                  bounded return package
                           |
                           v
              +---------------------------+
              |       MAIN CONVERSATION   |
              | - inspect result          |
              | - user can correct it     |
              | - retain useful findings |
              | - update structured state |
              +---------------------------+
                           |
                      next task
                           +----> create a completely new shadow
```

The main conversation persists. Each shadow execution is temporary. The shadow is not a permanent background observer or a second long-running agent.

## 5. Lifecycle

1. The main conversation maintains dialogue and structured context.
2. A bounded task is identified.
3. The main conversation assembles a task-specific input, including relevant context and references.
4. A fresh shadow is instantiated without prior shadow history.
5. The shadow performs the task and may use tools, retrieve material, execute code, and test.
6. The shadow returns the result and relevant structured conclusions, not its entire execution transcript.
7. The main conversation reviews the result; the user can identify and correct an incorrect judgment.
8. The main conversation retains useful information and updates its structured context.
9. The shadow run ends. A later task starts with a new shadow.

## 6. Responsibility boundaries

| Concern | Main conversation | Shadow |
|---|---|---|
| User-facing continuity | Owns | Does not own |
| Persistent dialogue/context | Maintains | No cross-task history |
| Structured context | Maintains and supplies | Consumes for current task |
| Task definition | Assigns | Executes |
| Tool calls and intermediate work | Need not retain | Performs within its run |
| Cross-task memory | Maintains | None |
| Result review and correction | Supports | Supplies result |
| Future task | Builds new input | Ends after current task |

Tool activity can occur inside a shadow without becoming part of the main conversation's ongoing execution transcript.

## 7. Proposed contracts

These are conceptual contracts for prototypes, not claims about existing platform features.

### Task context package
A package may contain:
- `task_id`: bounded task identifier;
- `objective`: requested outcome;
- `acceptance_criteria`: completion criteria;
- `relevant_context`: selected dialogue and structured context;
- `constraints`: hard requirements and prohibited actions;
- `references`: files, repository paths, URLs, or source material;
- `tool_permissions`: tools and access allowed;
- `output_contract`: required return format;
- `uncertainties`: known gaps that must not be silently guessed.

The package should be sufficient but focused. It should not indiscriminately copy the entire main-conversation transcript.

### Return package
A package may contain:
- `task_id` and `status` (completed, blocked, failed, or partial);
- `result`: user-relevant outcome;
- `findings`: evidence-supported conclusions;
- `recommendations`: distinguished from established facts;
- `assumptions` and `open_questions`;
- `evidence`: concise references to sources, files, commands, or tests;
- `artifacts`: paths or links to outputs;
- `context_update_candidates`: information potentially worth retaining.

The main conversation decides what to retain.

## 8. Retention principles

1. **Continuity information** — intent, durable constraints, accepted decisions, and current state — belongs in the main conversation's retained context.
2. **Task-local working information** — intermediate reasoning, tool output, retrieval noise, retries, temporary hypotheses, and execution logs — belongs to the temporary shadow run.
3. **Reusable outcomes** — findings and artifacts that may matter later — are returned in structured form for review and selective retention.

Durable project facts may also live in versioned external artifacts such as repository documents, specifications, or issue trackers. The architecture does not require model memory to be the sole system of record.

## 9. Failure modes and risks

- **Main conversation growth:** the persistent context can itself become noisy, stale, or diluted.
- **Bad source context:** a shadow may execute correctly against incorrect or outdated structured context.
- **Packaging omissions:** a fresh shadow cannot use a constraint it was not given unless it can retrieve it from an authorized source.
- **Incorrect shadow judgment:** a single run can still misunderstand the task or rely on weak evidence. Its result must be reviewable and correctable.
- **Over-compressed return:** a concise result may omit caveats or evidence.
- **Hidden runtime state:** tools, caches, files, memory stores, or agent runtimes may retain state outside the visible conversation; deployments must inspect these channels before claiming isolation.
- **Cost and latency:** fresh initialization and repeated packaging may add overhead.
- **Poor task boundaries:** overly broad tasks recreate long contexts; overly narrow tasks create excessive handoffs.

This design relocates and bounds execution context; it does not make context limitations disappear.

## 10. Experimental hypotheses

These are hypotheses, not established results.

- **H1:** fresh shadows prevent prior task execution traces from accumulating in later shadow runs.
- **H2:** focused task packages may improve retention of task-relevant constraints compared with a single long-running execution context.
- **H3:** task-local runs may make incorrect judgments easier to attribute and review.
- **H4:** degradation in the main conversation's retained context will still degrade shadow execution.
- **H5:** orchestration and repeated initialization may increase token use, latency, and operational complexity.

## 11. Evaluation proposal

### Baselines
Compare:
- **A — Long-running agent:** one agent conversation performs a sequence of tasks and retains execution history according to the platform's normal behavior.
- **B — Shadow architecture:** one persistent main conversation creates a fresh shadow per task and selectively retains returned conclusions.

Hold constant where possible: model/settings, task sequence, task difficulty, tools and permissions, source materials, acceptance criteria, and evaluation procedure. Document unavoidable runtime differences.

### Workload
Use repeatable multi-task workloads containing early constraints needed later, dependencies on accepted decisions, noisy tool output, misleading intermediate findings, and changes that require distinguishing current from stale assumptions. Run multiple trials and vary order where practical.

### Metrics

| Metric | Meaning | Example |
|---|---|---|
| Context growth | Retained context accumulation | Context tokens per task |
| Constraint retention | Compliance with required constraints | Critical-constraint pass rate |
| Task drift | Deviation from objective | Blinded rubric score |
| Repeated work | Re-execution of completed actions | Duplicate tool/action count |
| Error localization | Ability to attribute incorrect results | Reviewer attribution score |
| Result quality | Correctness and completeness | Acceptance-test pass rate |
| Handoff overhead | Packaging and return cost | Tokens, latency, handoff count |
| Total cost | Overall resource use | Tokens, tool cost, elapsed time |

Token reduction alone is not evidence of better performance. Quality, cost, and failure rates must be reported together.

### Reporting
Publish task fixtures, model/runtime configuration, prompts and context packages, scoring rubrics, raw measurements where safe, failed trials, deviations, limitations, and reproducibility notes. Do not select only successful examples.

## 12. Non-goals

This proposal is not:
- a background shadow agent continuously monitoring the main conversation;
- a permanent shadow agent with its own long-term history;
- a stateless main conversation;
- a claim that the main conversation cannot suffer attention dilution;
- a guarantee that shadow judgments are correct;
- a replacement for version control, project documentation, or systems of record;
- a claim that current commercial runtimes already provide the required isolation guarantees.

## 13. Open implementation questions

1. What is the minimum sufficient task package for each task class?
2. How should structured context remain compact, current, and auditable?
3. Which outcomes belong in the main conversation versus external artifacts?
4. How can a runtime guarantee that a shadow does not inherit prior shadow conversation state?
5. How should credentials, permissions, and filesystem access be scoped per task?
6. What evidence should accompany a shadow conclusion?
7. How should partial, blocked, and failed runs be represented?
8. When should a task be split across multiple fresh shadows?
9. How should inherently long-running tasks be handled?
10. How can attention dilution be operationalized and measured?

## 14. Prototype stages

- **Stage 0 — Specification:** agree on terms, boundaries, and task/return contracts.
- **Stage 1 — Manual simulation:** a human-operated main conversation prepares task packages and invokes independent fresh sessions.
- **Stage 2 — Instrumented comparison:** compare baseline and shadow workflows using repeatable tasks and recorded metrics.
- **Stage 3 — Runtime prototype:** automate shadow creation, packaging, return, and termination.
- **Stage 4 — Independent review:** invite external reviewers to reproduce, challenge, and extend the evaluation.

Do not present a prototype as proof until it has been evaluated against a documented baseline.

## 15. Review invitation

Feedback is welcome on the architecture boundary, practical task/return contracts, missing failure modes, fair baseline design, metrics for attention dilution and error localization, and runtimes capable of genuine per-task isolation.

Please distinguish conceptual objections, implementation constraints, and empirical results. The goal is a testable and falsifiable proposal, not a claim to defend.

## Change log

- **0.1 — 2026-11-04:** Initial RFC defining a persistent main conversation and fresh, stateless, single-task shadow execution.
