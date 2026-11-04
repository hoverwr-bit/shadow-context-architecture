# Runtime Adapter Contract (v0.1)

## Purpose

This document defines the boundary between a prepared Shadow task package and an execution provider. It does not introduce a persistent parent Agent, an orchestrator, or a hidden planning process. The cockpit remains a non-agent workspace; the runtime receives one explicit task package and returns one bounded result.

## Adapter contract

The provider-neutral contract is intentionally small:

- `build_request(package) -> provider_request`: deterministic and side-effect free.
- `execute(package) -> shadow-return-v1`: performs one isolated execution and may incur provider cost.
- `normalize(provider_response, package) -> shadow-return-v1`: validates run/task/snapshot identity before returning data to the cockpit.

The initial Python implementation exposes `RuntimeAdapter` and `OpenAIResponsesAdapter` in `demo/shadow_demo/runtime.py`. The Mock runner remains the lifecycle baseline.

## OpenAI Responses API request layout

The first adapter uses two messages:

1. Developer message: stable rules and project conventions, with an explicit `prompt_cache_breakpoint` on the final stable text content block.
2. User message: dynamic task objective and pinned project snapshot.

It sets:

- `prompt_cache_key` to a configured stable workspace-level key. It must not contain a run ID or task ID.
- `prompt_cache_options.mode = "explicit"` so a changing suffix does not create an implicit breakpoint.
- `prompt_cache_options.ttl = "30m"`.
- `store = false` and no provider tools in this first adapter.
- JSON-object output, followed by local validation against `shadow-return-v1`.

A fresh run changes only the dynamic suffix. The stable prefix, model, request shape, and cache key must remain identical for a controlled cache experiment. The key helps route similar requests; it is not a cache-hit guarantee.

## Telemetry

The normalizer records provider-reported:

- model and response ID
- elapsed request time
- input, cached, cache-write, output, and total tokens
- stable-prefix and dynamic-suffix SHA-256 hashes
- cache key and breakpoint mode

Cost is marked `not_computed`: token counts alone are insufficient without the applicable model price schedule and any other billable usage. Missing provider telemetry stays null or `not_available`; it is never inferred from byte counts.

## Identity and acceptance boundary

The normalizer rejects output whose `schema_version`, `task_id`, `run_id`, or `snapshot_id` does not match the submitted package. It does not apply proposed project updates. The existing cockpit-side inspect/accept flow and stale-snapshot guard remain the only route for project-file mutation.

## Deliberate v0.1 limitations

- No function tools, browser, filesystem, shell, credentials, or network access are exposed to the model.
- No retries or automatic fallback are performed.
- No API request is made by `build_request`; `execute` is the explicit billable boundary.
- `store=false` is an API response-storage setting, not a claim that all provider-side retention is disabled.
- The adapter does not claim to provide a secure execution sandbox. Production isolation and tool permissioning remain separate runtime responsibilities.
- Prompt-cache eligibility and telemetry can be tested here; cache hit rate and task quality still require live, controlled experiments.

## Test strategy

Unit tests must cover deterministic request construction, explicit breakpoint placement, stable cache-key reuse across fresh run IDs, provider telemetry extraction, and rejection of cross-run or cross-snapshot results. Live cache experiments must compare otherwise identical requests and record actual provider usage fields.
