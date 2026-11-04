# Cache Experiment: Fresh Shadows and Stable Prompt Prefixes

- Status: Provider-specific implementation note and proposed experiment
- Research snapshot: 2026-11-04
- Scope: OpenAI API prompt caching; other providers may behave differently
- Related: [RFC](RFC.md), [Architecture](ARCHITECTURE.md), [Experiment protocol](EXPERIMENTS.md), [Runnable demo](demo/README.md)

## 1. Short answer

**Creating a new Shadow execution context does not, by itself, imply a prompt-cache miss.**

Prompt caching is based on reuse of an eligible matching prompt prefix, not on preserving the same conversational agent instance. A fresh Shadow can send the same stable prefix again and may reuse cached model state if the provider can route the request to a machine holding a matching, unexpired entry.

A cache hit is not guaranteed. The complete rendered prefix, cache breakpoint, model and relevant settings must match; cache routing, expiry, traffic, organization, and region can also affect reuse.

For OpenAI's current documentation, see [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

## 2. Provider behavior that matters

The following points are specific to the OpenAI API documentation available on the research date:

1. **Exact prefix matching.** Static instructions, shared references, tool definitions, and other reusable content should appear before dynamic task/project content. Relevant tools and schemas must also remain identical for the prefix to match.
2. **Cache breakpoints matter.** For GPT-5.6 and later model families, the default implicit breakpoint is placed at the latest user or tool message. A changed suffix can therefore prevent reuse of a long common prefix if no explicit breakpoint marks the stable boundary.
3. **Mark the stable boundary.** Put an explicit `prompt_cache_breakpoint` at the end of the stable prompt content. For a prefix-only cache strategy, use `prompt_cache_options.mode: "explicit"` so the changing suffix is not itself written as an implicit cache endpoint.
4. **Use a stable routing key.** Reuse a `prompt_cache_key` for requests that share the prefix. It helps route related requests to the same cache but does not guarantee a hit. Do not create a unique key for every Shadow run; that would fragment reuse. A stable workspace/prompt-version key is a reasonable experiment arm.
5. **Minimum size.** GPT-5.6 and later require at least 1,024 visible input tokens in the prefix. The demo's byte counts and SHA-256 values do not prove that this threshold is met; count tokens with the actual model/tokenizer.
6. **Routing and locality.** Cache entries are machine-local. Requests may miss if they are routed elsewhere, if the entry expired, or if traffic for a key is too high. The documentation recommends keeping traffic around 15 requests per minute per key and partitioning higher-volume traffic with stable keys.
7. **Measure actual usage.** Inspect `usage.input_tokens_details.cached_tokens` and `cache_write_tokens` (or the corresponding API-specific usage fields), plus latency and cost. A matching local hash is not a cache-hit measurement.

The current documentation also states that caches are not shared across organizations or regional processing boundaries. Cache lifetime and write pricing vary by model family and request settings; verify current model-specific documentation before selecting them.

## 3. Mapping to Shadow Context Architecture

Recommended prompt layers:

```text
[Provider hidden instructions / fixed API configuration]
[Stable system and developer rules]
[Stable project conventions and output contract]
[Explicit cache breakpoint]
-----------------------------------------------
[Current project-state snapshot]
[Task objective and acceptance criteria]
[Task-specific authorized references]
```

The top layer must be stable across Shadow runs. The lower section is task-specific and can change without invalidating the explicitly marked stable prefix.

Important implementation details:

- Keep model, tool definitions, structured-output schema, and other prefix-affecting settings stable across comparable runs.
- Keep timestamps, run IDs, task IDs, project-state snapshots, and user-specific dynamic material after the stable breakpoint.
- If project conventions change, version the stable prefix. The first request with the new version is expected to write a new cache entry.
- Keep a stable cache key at the project/workspace + prompt-version scope when appropriate; never use a per-run random key for the reuse experiment.
- The cockpit and Shadow lifecycle remain independent of the cache. Cache availability must never be required for correctness.

## 4. Experiment arms

Use the same model, organization, region, tools, output schema, and task sequence wherever possible.

| Arm | Prompt structure | Cache configuration | Question |
|---|---|---|---|
| K0 | Stable and dynamic content mixed | Provider default | Baseline cache behavior |
| K1 | Stable prefix first, dynamic suffix last | Implicit/default breakpoint | Does ordering alone help? |
| K2 | Stable prefix first, explicit breakpoint | Explicit breakpoint, stable key | Can fresh Shadows reuse the marked prefix? |
| K3 | Same as K2, but new key per run | Explicit breakpoint, per-run key | Does key fragmentation reduce reuse? |
| K4 | Same as K2, but change tool schema/model | Explicit breakpoint, stable key | How much does prefix-affecting configuration invalidate reuse? |

Do not infer a hit from response latency. Use provider usage telemetry. Repeat requests across several Shadow instances, with controlled intervals inside and beyond documented cache lifetimes.

## 5. Required measurements

For each request, record:

- run ID and task ID;
- model and model version;
- organization/region where available;
- tool-schema hash and structured-output-schema hash;
- stable-prefix hash and token count;
- dynamic-suffix hash and token count;
- cache key and breakpoint configuration;
- elapsed time since the previous matching request;
- input tokens, cached tokens, cache-write tokens, output tokens;
- time to first token and total latency;
- uncached cost, cache-read cost, cache-write cost, and total cost.

Report both cache-hit ratio and absolute cached tokens. A high ratio on a tiny prefix may save little; a lower ratio on a large prefix may still be valuable.

## 6. Falsifiable hypotheses

- K2 can achieve non-zero cached input tokens across separate Shadow runs when the stable prefix is long enough, identical, explicitly marked, and routed to an eligible cache entry.
- K3 will reduce reuse compared with K2 when per-run keys fragment routing.
- K4 will reduce or reset reuse when a changed tool schema/model changes the rendered prefix.
- Cache misses can still occur under K2 because routing and cache residency are not guaranteed.
- Total cost may not improve if cache writes, short reuse windows, or handoff overhead outweigh cache-read savings.

## 7. What the current demo proves—and does not prove

The runnable demo now:
- keeps stable rules/conventions before the dynamic task/project snapshot;
- records stable-prefix and dynamic-suffix hashes and byte lengths;
- tests that project-state changes alter the suffix but not the stable prefix.

It does **not**:
- call the OpenAI API;
- count model tokens;
- insert an API-level cache breakpoint;
- set a `prompt_cache_key`;
- observe `cached_tokens` or `cache_write_tokens`;
- claim any real cache hit.

The next provider integration should add an adapter that sends the serialized prompt with the provider's explicit cache boundary and captures usage telemetry. Until then, cache behavior remains an unmeasured hypothesis.

## 8. Reference

- OpenAI, [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), consulted 2026-11-04.
