# Cache Experiment Harness

## Purpose

The harness is an external measurement tool, not an Agent and not part of the cockpit's task orchestration. It creates independent request cases, executes them only after an explicit flag, and stores provider telemetry.

## Experiment arms

| Arm | Prompt layout | Cache controls | Isolated variable |
|---|---|---|---|
| K0 | Stable + dynamic text in one user message | Provider defaults; no key | Mixed-prompt baseline |
| K1 | Stable developer message, dynamic user message | Implicit mode; stable arm key | Message ordering without explicit boundary |
| K2 | Stable developer content with explicit breakpoint, then dynamic user message | Explicit mode; stable arm key | Intended stable-prefix reuse |
| K3 | Same as K2 | Explicit mode; a different key for each run | Cache-key fragmentation |
| K4 | Stable prefix changed, then dynamic user message | Explicit mode; same key as K2; compares against latest K2 response | Prefix-version invalidation |

Each arm runs at least two fresh request instances. Each request has a unique run ID in the dynamic suffix. No prior response text or conversation history is resent.

K4 changes only stable-prefix text in this first version. It does not mutate tool definitions or model selection, because the adapter intentionally exposes no tools.

## Run it

Create two text files:
- stable-prefix.txt: the reusable system/developer rules and project conventions.
- dynamic-suffix.txt: a representative task/project-state payload.

For GPT-5.6 and later, current documentation specifies at least 1,024 visible input tokens for caching. The harness does not guess token counts from bytes or characters. Verify actual input_tokens from provider usage before interpreting misses.

Create a plan (no API request is sent):

\`\`\`bash
PYTHONPATH=demo python -m shadow_demo.cache_harness plan \\
  --prefix-file ./stable-prefix.txt \\
  --dynamic-file ./dynamic-suffix.txt \\
  --model your-enabled-model-id \\
  --cache-key shadow-workspace-cache-v1 \\
  --repeats 3 \\
  --output ./cache-plan.json
\`\`\`

Render all request bodies without sending them:

\`\`\`bash
PYTHONPATH=demo python -m shadow_demo.cache_harness run \\
  --plan ./cache-plan.json \\
  --output-dir ./cache-results
\`\`\`

Only when ready to incur API usage, explicitly execute:

\`\`\`bash
OPENAI_API_KEY=... PYTHONPATH=demo python -m shadow_demo.cache_harness run \\
  --plan ./cache-plan.json \\
  --output-dir ./cache-results \\
  --execute
\`\`\`

The output directory contains requests/ (exact request bodies), records.jsonl (one telemetry record per attempted request), summary.json (aggregate metrics), or dry_run.json when no execution is requested.

## Measurements

The harness records input/cached/write/output tokens, TTL-specific cache-write token counts, latency, model and response IDs, cache key, breakpoint mode, stable/dynamic hashes, and prompt-cache diagnostics (cache_hit, cache_miss, reason, reusable tokens, missed tokens).

The reported cache-hit ratio is aggregate cached input tokens divided by aggregate input tokens, not a request-count ratio. Costs are marked not_computed; apply the exact model/date price schedule separately.

A cache_hit diagnostic means no miss was detected relative to the selected baseline. It does not mean every input token was cached. Use cached_tokens for actual reuse volume. Diagnostics are best-effort and may be unavailable.

## Experimental controls

- Keep model, service tier, organization, region, and request settings constant where intended.
- Use a representative stable prefix and confirm its actual token size.
- Run K2 requests close enough together to test cache residency, then repeat at planned intervals.
- Do not run arms concurrently when comparing cache writes/reuse; concurrent requests can race and affect routing.
- Treat latency as secondary; never infer cache hits from latency alone.
- Repeat the experiment at another time before making a general claim.

## Safety and cost boundary

Planning and dry-run rendering are local and do not incur API usage. Network execution is gated behind --execute, requires OPENAI_API_KEY, and may incur input, cache-write, cache-read, and output charges. No automatic retries are performed. Do not put secrets in prompt files.

The request uses store=false. This controls API response storage behavior; it does not imply that all provider-side retention is disabled.
