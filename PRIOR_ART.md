# Prior Art: Context Isolation, Sub-agents, and Persistent Orchestration

- Status: Preliminary literature and product scan
- Research snapshot: 2026-11-04
- Scope: Public documentation and engineering articles reviewed for conceptual overlap
- Related documents: [RFC.md](./RFC.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [EXPERIMENTS.md](./EXPERIMENTS.md)

## 1. Executive finding

The core mechanism proposed by Shadow Context Architecture is **not novel in isolation**.

Fresh task-scoped contexts, isolated sub-agents, persistent orchestrators, and returning concise results to a parent conversation are already present in public agent products and frameworks. The closest overlap found in this scan is Claude Code Sub-agents. Anthropic's long-running-agent harness also describes context resets with structured handoffs. OpenAI's multi-agent documentation describes independent sub-agent contexts coordinated by a main agent.

This does not establish that every detail of this proposal is identical to an existing implementation. It does mean the project must not claim invention of:
- fresh context windows for delegated work;
- parent/child agent orchestration;
- keeping sub-agent intermediate work out of the main conversation;
- returning a summary or final result to the main agent;
- context reset plus structured handoff as a long-running-work technique.

The defensible contribution, if further specified and validated, is better framed as an **explicit operating contract and evaluation protocol** for a persistent conversational continuity owner that dispatches a fresh, stateless execution instance for each bounded task.

This is a preliminary scan, not a systematic literature review or patent search. Absence of a match in this document is not proof that no prior implementation exists.

## 2. Closest prior art

| System / source | Documented mechanism | Overlap | Important distinction or open question |
|---|---|---|---|
| Claude Code Sub-agents | Each sub-agent has its own context; starts fresh without the parent conversation; works independently; only its result is returned to the main conversation | Very high | This is the closest product-level match to the task-local shadow lifecycle and return boundary. The exact persistence, reuse, and runtime guarantees should be checked against the implementation/version under test. |
| Anthropic long-running-agent harness | Context resets clear the context and start a fresh agent, with structured handoff artifacts carrying prior state and next steps | Very high | Focuses on continuing a long-running project across agent sessions, rather than explicitly defining a persistent user-facing conversation as the sole continuity owner for every bounded task. |
| OpenAI Agents API Multi-agent | Main agent delegates to independent sub-agents with their own contexts; main coordinates and combines results | Very high | Documents the core parent/sub-agent split. The proposal's stricter per-task lifecycle and no cross-task shadow history need to be treated as explicit invariants, not assumed from the generic multi-agent pattern. |
| Anthropic context engineering / sub-agent architectures | Focused sub-agents use clean contexts and return distilled summaries to a lead agent | High | Describes the general pattern and rationale, rather than the complete lifecycle contract proposed here. |
| OpenAI Agents SDK Sessions | Sessions preserve conversation history across runs; context can be trimmed or summarized | Partial | A persistent-session strategy for continuity, not itself a fresh-per-task execution architecture. |
| OpenAI Agents SDK Handoffs | Handoff can transfer conversation control; by default the receiving agent sees conversation history unless input filtering changes it | Partial / contrasting | Demonstrates that “handoff” does not automatically mean context isolation. The input boundary must be explicit. |
| Google ADK | Agents can communicate through shared invocation/session state; workflow agents can pass state between steps | Partial | Shared state is a different choice from strict task-local execution contexts. |
| LangGraph Persistence | Checkpointers preserve thread-scoped graph state; stores hold longer-term cross-thread data | Partial | Provides persistence primitives and memory scopes, not the complete shadow lifecycle by itself. |

## 3. Source notes

### 3.1 Claude Code Sub-agents — closest match

Anthropic's public guide describes sub-agents as isolated instances with their own context windows. A sub-agent starts fresh without the parent conversation history, performs its task, and returns only the relevant result to the main conversation. The guide explicitly positions this as a way to keep research, logs, and other noisy work out of the main thread.

Source:
- [How and when to use subagents in Claude Code](https://claude.com/resources/articles/subagents-in-claude-code)

A separate Anthropic article describes sub-agents as a way to move noisy work into another context, with only the answer returning to the main session:
- [Maximizing the value of your Claude Code sessions](https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions)

**Assessment:** The proposal's “fresh worker, isolated execution, result-only return” is already a documented product pattern. Any novelty claim must go beyond those mechanics.

### 3.2 Anthropic long-running-agent harness

Anthropic describes context resets as clearing the context window and starting a fresh agent, combined with a structured handoff containing the previous agent's state and next steps. It contrasts this with compaction, which shortens history in place but does not create a clean slate.

Source:
- [Harness design for long-running apps](https://www.anthropic.com/research/harness-design-long-running-apps)
- [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)

**Assessment:** Context reset plus structured handoff is established prior art. The proposal should distinguish task-by-task ephemeral execution from a sequence of sessions that continue one long-running project through durable progress artifacts.

### 3.3 OpenAI Multi-agent

OpenAI documents a multi-agent pattern in which an agent delegates work to independent sub-agents. Each sub-agent has its own context, can work in parallel, and the main agent coordinates and combines the results.

Source:
- [Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent)

**Assessment:** The parent coordinator and independent worker split is established prior art. The proposal's value, if any, lies in making strict lifecycle, context ownership, and evaluation rules explicit.

### 3.4 OpenAI Sessions and Handoffs

The Agents SDK Sessions documentation describes preserving conversation history across runs. OpenAI's context-management cookbook discusses trimming and summarization, including the risks of carrying too much history or losing important facts.

Sources:
- [Agents SDK Sessions](https://openai.github.io/openai-agents-python/sessions/)
- [Context Engineering: Short-Term Memory Management with Sessions](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory)

OpenAI's Handoffs documentation notes that a receiving agent normally sees the conversation history unless an input filter or related configuration changes what is passed.

Source:
- [Agents SDK Handoffs](https://openai.github.io/openai-agents-python/handoffs/)

**Assessment:** These documents show why context continuity and execution isolation must be treated as separate design decisions. A handoff alone is not proof of a clean context.

### 3.5 Google ADK and LangGraph

Google ADK documents shared session state and invocation context as mechanisms for communication between agents and workflow steps.

Source:
- [Google ADK custom agents](https://github.com/google/adk-docs/blob/main/docs/agents/custom-agents.md)

LangGraph documents thread-scoped checkpoint persistence and longer-term stores.

Source:
- [LangGraph persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx)

**Assessment:** These are relevant state-management primitives, but they do not by themselves establish the complete per-task ephemeral shadow model.

## 4. What may still distinguish this proposal

The following are candidate differentiators to specify and test. They are **not claims of proven originality**.

1. **One explicit continuity owner.** The persistent main conversation is the sole conversational continuity owner. Shadows do not become peer long-lived agents and do not maintain cross-task execution history.
2. **Fresh instance for every bounded task.** The lifecycle rule is mandatory, not merely an optional optimization used when a coordinator decides delegation is convenient.
3. **No execution-trace backflow by default.** Tool calls, search trails, intermediate outputs, and task-local logs remain outside the main conversation. Only a bounded return package is passed back.
4. **User-visible correction loop.** The main conversation presents the shadow's conclusion so the user can identify a wrong judgment; corrections then update the persistent conversation's structured context.
5. **Explicit context ownership contract.** The design distinguishes persistent dialogue/continuity, task input, task-local execution state, durable external artifacts, and returned conclusions.
6. **Longitudinal evaluation target.** The proposed experiment measures whether this arrangement reduces cross-task contamination and late-sequence drift, while separately measuring whether the persistent main conversation itself becomes a bottleneck.

Items 1–5 may already be achievable with existing sub-agent systems. The likely contribution is therefore a clear, testable architecture profile and evaluation method, not necessarily a new runtime primitive.

## 5. The strongest challenge the project must answer

> Why is this more than using Claude Code Sub-agents or OpenAI Multi-agent with a persistent coordinator?

A credible answer cannot be “because the worker is called a shadow.” It must specify operational invariants and demonstrate a measurable advantage over a well-configured sub-agent baseline.

At minimum, a comparative implementation should test:

- Does every bounded task receive a genuinely new execution context?
- Can any previous shadow transcript, hidden memory, or tool session leak into the next shadow?
- Does the main conversation receive only the agreed return package, rather than the worker's raw execution trace?
- How is the persistent main context kept accurate as it accumulates user dialogue and accepted conclusions?
- Does user correction propagate reliably to later tasks?
- Does this improve late-sequence task quality, constraint retention, or error localization enough to justify packaging, orchestration, and token overhead?

A baseline using existing sub-agents must be configured competently. Comparing against a deliberately poor single-agent baseline would not establish a meaningful contribution.

## 6. Revised positioning

Recommended project description:

> Shadow Context Architecture is an experimental operating model for long-running AI work. It makes conversational continuity the responsibility of one persistent main session, while each bounded task is executed by a fresh, disposable worker context. The worker's intermediate execution trace stays isolated; only a structured result returns for review and possible incorporation into the main session.
>
> The proposal does not claim to invent sub-agents or context resets. It asks whether enforcing this lifecycle as a consistent context-ownership contract can measurably reduce cross-task context contamination, improve error localization, and preserve task quality over long interaction sequences.

Recommended claim level:
- **Safe to claim:** This repository proposes and specifies an explicit architecture profile and a validation protocol.
- **Requires implementation evidence:** A given runtime actually enforces the isolation and lifecycle invariants.
- **Requires comparative experimental evidence:** The architecture improves reliability, drift, or error localization over existing sub-agent approaches.
- **Do not claim yet:** The design is novel, solves context dilution, or outperforms existing agent frameworks.

## 7. Limitations of this scan

- This is a targeted scan of public product documentation and engineering articles, not a systematic academic survey.
- Product behavior may change; implementation-specific claims should be pinned to tested versions.
- Public documentation may omit internal runtime details.
- No patent, academic citation graph, or exhaustive open-source implementation search was performed.
- Similarity of concepts does not prove identical implementation, and different names do not prove novelty.

## 8. References

1. Anthropic, [How and when to use subagents in Claude Code](https://claude.com/resources/articles/subagents-in-claude-code).
2. Anthropic, [Maximizing the value of your Claude Code sessions](https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions).
3. Anthropic, [Harness design for long-running apps](https://www.anthropic.com/research/harness-design-long-running-apps).
4. Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents).
5. OpenAI, [Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent).
6. OpenAI, [Agents SDK Sessions](https://openai.github.io/openai-agents-python/sessions/).
7. OpenAI, [Context Engineering: Short-Term Memory Management with Sessions](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory).
8. OpenAI, [Agents SDK Handoffs](https://openai.github.io/openai-agents-python/handoffs/).
9. Google, [ADK custom agents](https://github.com/google/adk-docs/blob/main/docs/agents/custom-agents.md).
10. LangChain, [LangGraph persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx).
