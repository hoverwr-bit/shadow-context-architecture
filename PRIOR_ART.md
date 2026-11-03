# Prior Art: Context Isolation, Project-State Continuity, and Agent Orchestration

- Status: Preliminary literature and product scan
- Research snapshot: 2026-11-04
- Related documents: [RFC.md](./RFC.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [EXPERIMENTS.md](./EXPERIMENTS.md)

## 1. Executive finding

The previous draft compared the proposal to sub-agent systems as though it were a persistent main Agent delegating work. That framing was incorrect and is withdrawn.

The proposal now being evaluated is materially different in its role separation:
- the persistent cockpit is a structured user-facing workspace, not an Agent or orchestrator;
- versioned project files, rather than the conversation transcript, hold durable project state and current focus;
- a fresh shadow execution context performs each bounded task;
- the dispatch/runtime mechanism is separate and intentionally unspecified at this stage;
- only a bounded, reviewable result returns to the cockpit, and accepted project changes are versioned.

This distinction does not make the underlying mechanisms unprecedented. Fresh contexts, external artifacts, structured handoffs, sub-agents, and workflow runtimes are established areas of prior art. The question is whether this exact operating model and its measurable properties offer a useful contribution.

## 2. Comparison

| System / pattern | Publicly documented mechanism | Relationship to this proposal | Important distinction / unknown |
|---|---|---|---|
| Claude Code Sub-agents | Isolated sub-agent contexts; fresh workers can perform delegated tasks and return results to a main conversation | Strong overlap in disposable execution and trace containment | The documented parent remains an Agentic conversation. This proposal's cockpit is not a parent Agent; project files are the continuity substrate. |
| Anthropic long-running-agent harness | Context resets with structured handoff artifacts and durable progress information | Strong overlap in fresh execution and externalized state | Primarily addresses continuity across successive agent sessions. This proposal applies task-scoped disposal while the user-facing cockpit remains a non-agent workspace. |
| OpenAI multi-agent patterns | A main Agent delegates to independent sub-agents and coordinates results | Overlap in independent task contexts | The main Agent/coordinator role is specifically absent from the proposed cockpit. |
| OpenAI Agents SDK Sessions / Handoffs | Persistent sessions, conversation history, handoff and input filtering | Relevant context-continuity and transfer primitives | These mechanisms do not by themselves define a non-agent cockpit backed by project files. Handoff alone does not prove isolation. |
| Google ADK | Agent workflows and shared session/invocation state | Relevant workflow and state primitives | Shared state and agent workflow composition differ from the proposed explicit project-file source of truth and disposable task context. |
| LangGraph persistence | Thread-scoped checkpoints and longer-term stores | Relevant persistence primitives | Persistence primitives can support external state, but do not prescribe this complete role separation. |

This is a targeted scan, not a systematic academic survey, patent search, or exhaustive implementation search. Product behavior should be checked against the exact version used in any implementation.

## 3. What is already established prior art

The project must not claim to have invented:
- fresh context windows or isolated sub-agent execution;
- context reset and structured handoff;
- external project files or durable state artifacts;
- returning concise results instead of full execution traces;
- workflow engines that launch and monitor task executions;
- prompt-prefix caching or stable-prefix prompt organization.

## 4. Candidate distinction to investigate

The candidate contribution is the combined architecture contract:

1. **Non-agent cockpit:** persistent user-facing interaction remains a structured workspace rather than an autonomous control agent.
2. **Project-file focus:** active project state and current focus are explicit, versioned artifacts, not something reconstructed from a long conversation transcript.
3. **Ephemeral task execution:** every bounded task starts a fresh shadow context, with no inherited prior shadow execution history.
4. **No automatic trace backflow:** raw tool traces and intermediate work do not become cockpit history by default.
5. **Human-visible correction:** results are presented for inspection; accepted corrections update authoritative project files.
6. **Cache-aware but cache-independent execution:** stable prompt prefixes may be reused where supported, without depending on cache state for correctness.
7. **Evaluation of the whole lifecycle:** compare focus stability, project-state integrity, isolation, cache behavior, error localization, and total cost against competent sub-agent baselines.

These are candidate differentiators, not proof of novelty. Some or all may be implementable using existing tools and frameworks.

## 5. The key comparison question

> Does a non-agent cockpit backed by versioned project state, combined with disposable task execution and a separate dispatch mechanism, provide measurable benefits over a conventional parent-Agent/sub-agent architecture?

A fair baseline must be competently configured. It should not be intentionally weakened by poor context curation or excessive transcript retention.

The evaluation should test whether project state remains accurate; whether tasks start from explicit reproducible snapshots; whether the cockpit avoids execution noise; whether task focus and late-sequence quality improve; whether dispatch and packaging overhead outweigh benefits; whether cache reuse is retained; and whether existing frameworks can implement the same role separation without material changes.

## 6. Recommended claim level

- **Safe to claim:** This repository proposes a specific separation of cockpit, project-state artifacts, dispatch/runtime, and ephemeral execution, plus an evaluation protocol.
- **Requires implementation evidence:** A runtime actually enforces the specified isolation and lifecycle.
- **Requires comparative evidence:** The model improves focus stability, error localization, or total efficiency over competent alternatives.
- **Do not claim yet:** The architecture is unprecedented, guarantees constant context size, guarantees cache hits, or outperforms existing frameworks.

## 7. References

- Anthropic, [How and when to use subagents in Claude Code](https://claude.com/resources/articles/subagents-in-claude-code).
- Anthropic, [Harness design for long-running apps](https://www.anthropic.com/research/harness-design-long-running-apps).
- Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents).
- OpenAI, [Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent).
- OpenAI, [Agents SDK Sessions](https://openai.github.io/openai-agents-python/sessions/).
- OpenAI, [Agents SDK Handoffs](https://openai.github.io/openai-agents-python/handoffs/).
- Google, [ADK custom agents](https://github.com/google/adk-docs/blob/main/docs/agents/custom-agents.md).
- LangChain, [LangGraph persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx).

## 8. Limitations

This scan is preliminary. It does not establish novelty, non-obviousness, patentability, or exhaustive absence of similar systems. Similarity of individual mechanisms does not prove identical architecture; different terminology does not prove a new contribution.
