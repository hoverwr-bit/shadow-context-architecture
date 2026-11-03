# Experiments: Evaluating Shadow Context Architecture

- Status: Proposed protocol; no results claimed
- Version: 0.1
- Related documents: [RFC.md](./RFC.md), [ARCHITECTURE.md](./ARCHITECTURE.md)

## 1. Purpose

This document proposes a reproducible comparison between a conventional long-running agent workflow and a workflow with a persistent main conversation plus fresh, task-scoped shadow agents.

The experiment must test both benefits and costs. It must be possible for results to show that the architecture does not help, helps only for some task classes, or introduces unacceptable overhead.

## 2. Research questions

- **RQ1 — Context accumulation:** Does fresh-per-task execution prevent previous task tool traces and intermediate work from accumulating in later execution contexts?
- **RQ2 — Constraint retention:** Does a focused task package improve adherence to constraints that remain relevant across a sequence of tasks?
- **RQ3 — Drift:** Does the architecture reduce degradation in task alignment over a long task sequence?
- **RQ4 — Error localization:** Can reviewers more reliably identify which task or context package introduced an incorrect conclusion?
- **RQ5 — Trade-offs:** What additional token, latency, orchestration, and tool costs are introduced?
- **RQ6 — Main-context limits:** How does performance change as the persistent main conversation's own context grows or becomes inaccurate?

## 3. Conditions

### Condition A — Long-running agent baseline

One agent conversation performs the entire task sequence. It receives the same initial project information and tool permissions and retains context according to the baseline runtime's normal behavior.

### Condition B — Shadow workflow

A persistent main conversation maintains continuity and dispatches a newly initialized shadow for each task. Each shadow receives a task package assembled from the main conversation's current context. Only the structured return package is added to the main conversation; the shadow's full intermediate execution trace is not.

### Optional diagnostic condition C — Fresh agent without persistent orchestration

A new independent agent is started for every task but receives only the task prompt and static source material, without a persistent main conversation maintaining structured continuity. This condition is optional and helps distinguish the value of fresh execution from the value of persistent orchestration.

Do not compare B against C alone and claim the effect of the complete architecture. The primary comparison is A versus B.

## 4. Controls

Hold constant where feasible:
- model version and inference settings;
- task sequence and task difficulty;
- initial project facts and source documents;
- tool set, permissions, and tool versions;
- acceptance criteria and evaluator rubric;
- external environment and test fixtures.

Record all differences that cannot be held constant, including runtime context policies, hidden memory behavior, tool-session persistence, and token accounting. Randomize condition order where practical. Use multiple independent runs rather than relying on a single demonstration.

## 5. Workload design

Build a task sequence with a known ground truth and explicit scoring criteria. Include:

1. **Persistent constraints:** important requirements introduced early and needed again many tasks later.
2. **Decision dependencies:** later tasks depend on earlier accepted decisions.
3. **Irrelevant noise:** tool output and retrieved material that are not needed for the task.
4. **Misleading evidence:** plausible but incorrect findings that should be challenged.
5. **State changes:** a project fact changes, requiring the agent to distinguish current from stale information.
6. **Correction events:** the user corrects an earlier mistaken assumption; later tasks must use the correction.
7. **Cross-task reuse:** an earlier artifact is legitimately needed by a later task.
8. **Task boundary variation:** include narrow tasks and broader tasks to expose packaging and handoff costs.

Avoid designing every task to favor the shadow workflow. Publish the task sequence and scoring rubric before examining comparative results.

## 6. Metrics and operational definitions

| Metric | Operational definition | Reporting |
|---|---|---|
| Context accumulation | Tokens or equivalent context units retained in the active execution context over task index | Per-task curve and total |
| Main-context growth | Persistent main conversation context size over task index | Per-task curve |
| Constraint adherence | Fraction of applicable critical constraints satisfied | Pass rate and failure examples |
| Task quality | Blinded score against task-specific acceptance criteria | Mean, distribution, rubric |
| Task drift | Increase in objective deviation across sequence position | Score by task index |
| Repeated work | Duplicate completed actions not required by changed state | Count per task |
| Error localization | Reviewer's ability to identify the task/package associated with an injected or observed error | Accuracy and time |
| Correction propagation | Whether an explicit user correction is respected by later tasks | Pass rate |
| Handoff overhead | Context packaging and result transfer tokens, time, and operations | Per-task and total |
| End-to-end cost | Model tokens, tool cost, wall-clock time, and orchestration cost | Per-task and total |
| Isolation compliance | Whether a shadow can access prior shadow conversation state | Pass/fail from runtime tests |

Do not equate lower token count with better quality. Report quality, reliability, and cost together.

## 7. Measuring attention dilution

Attention dilution is not directly observable as one scalar. Use behavioral proxies rather than claiming to measure an internal model state directly.

Suggested proxies:
- missed critical constraints;
- increased reliance on stale facts;
- increased task drift;
- failure to apply explicit corrections;
- repeated rediscovery of already established facts;
- increased variance in task quality as the sequence progresses.

Report these as observable behavioral outcomes, not as direct measurements of attention itself.

## 8. Isolation tests

Before evaluating task quality, verify the runtime boundary:

1. Run shadow 1 and create a unique harmless marker in its conversation-only context.
2. Start shadow 2 with a task package that does not contain the marker and without access to shadow 1's transcript.
3. Ask shadow 2 whether it has the marker or prior-task context.
4. Repeat with memory, tool sessions, temporary files, caches, and other state channels where the runtime exposes them.
5. Record which channels are isolated, shared, or unknown.

A model's statement that it has no memory is not sufficient proof. The runtime configuration and observable access controls must support the claim. Do not put secrets or sensitive data in isolation markers.

## 9. Error localization protocol

Create a set of controlled errors, such as:
- a stale fact included in one task package;
- a misleading tool result in one shadow run;
- an incorrect conclusion in one return package;
- an omitted constraint during packaging.

Give reviewers the relevant task packages, return packages, and available evidence without telling them which condition produced the error. Ask them to identify the likely point of introduction, the evidence needed to confirm it, and the scope of downstream impact.

Score attribution accuracy and time-to-localize. Preserve ambiguous cases rather than forcing a single attribution.

## 10. Analysis plan

- Pre-register hypotheses, workload, exclusion rules, and scoring rubric before running the main comparison.
- Use paired task sequences where possible so conditions face equivalent work.
- Report per-task and aggregate results.
- Show distributions and uncertainty, not only averages.
- Separate task-quality outcomes from token/cost outcomes.
- Analyze early versus late tasks to identify sequence effects.
- Report main-context growth separately from shadow-context size.
- Include failures, blocked tasks, missing data, and protocol deviations.
- Avoid causal claims if runtime differences or unequal context inputs confound the comparison.

For small exploratory pilots, label results as preliminary and avoid statistical overstatement.

## 11. Minimum result table

| Category | Condition A | Condition B | Notes |
|---|---:|---:|---|
| Task acceptance rate | TBD | TBD | Same rubric |
| Critical constraint pass rate | TBD | TBD | Applicable constraints only |
| Late-sequence drift score | TBD | TBD | Blinded evaluation |
| Duplicate action count | TBD | TBD | Normalize by task count |
| Error localization accuracy | TBD | TBD | Controlled error set |
| Execution context tokens | TBD | TBD | Per-task and total |
| Main context tokens | N/A or runtime equivalent | TBD | Record actual availability |
| Handoff overhead | TBD | TBD | Include packaging and return |
| End-to-end cost | TBD | TBD | Tokens, tools, latency |
| Isolation test result | N/A | TBD | Document verified channels |

Do not fill TBD cells with estimates. Publish raw measurements and explain unavailable metrics.

## 12. Threats to validity

- **Model nondeterminism:** repeated runs may vary substantially.
- **Unequal context quality:** the shadow condition may benefit from more carefully curated inputs.
- **Runtime confounds:** hidden memory or tool-session behavior may differ between conditions.
- **Task representativeness:** a synthetic workload may not reflect real engineering or knowledge work.
- **Evaluator bias:** reviewers may favor a novel architecture; use blinded scoring where possible.
- **Token accounting gaps:** platforms may not expose all context or hidden runtime costs.
- **Task granularity:** results may depend heavily on how tasks are split.
- **Main-context bottleneck:** a degraded main conversation can contaminate every later task package.

## 13. Suggested pilot

A small first pilot can use:
- 1 documented task sequence of 12–20 tasks;
- 3 independent runs per condition as an exploratory minimum;
- one fixed model/runtime configuration where possible;
- a pre-written constraint checklist and acceptance rubric;
- at least 2 reviewers for a subset of quality and error-localization scoring.

This is a feasibility pilot, not enough by itself to establish general superiority. Increase runs and workload diversity before drawing strong conclusions.

## 14. Publication checklist

- [ ] Publish task fixtures and source materials, subject to licensing and privacy.
- [ ] Publish exact prompts and task context packages.
- [ ] Record model, runtime, tool, and permission configuration.
- [ ] Publish the scoring rubric before evaluating outputs.
- [ ] Record all trials, including failed and blocked runs.
- [ ] Report context growth, quality, isolation, and cost separately.
- [ ] Identify unobservable or unmeasured runtime state.
- [ ] Document deviations and limitations.
- [ ] Invite independent reproduction and critical review.

## 15. Current status

No empirical results are claimed in this document. All metrics and procedures are proposals until a pilot is executed and its evidence is published.
