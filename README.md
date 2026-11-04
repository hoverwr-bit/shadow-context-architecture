# Shadow Context Architecture

An experimental architecture proposal separating a persistent **structured cockpit** from disposable, task-scoped execution contexts.

- [RFC](RFC.md)
- [Architecture](ARCHITECTURE.md)
- [Prior-art scan](PRIOR_ART.md)
- [Experiment protocol](EXPERIMENTS.md)
- [Cache experiment and provider notes](CACHE_EXPERIMENT.md)
- [Runtime adapter contract](RUNTIME_ADAPTER.md)
- [Minimal runnable lifecycle demo](demo/README.md)

The cockpit is not a main Agent or orchestrator. Versioned project files hold durable project state. Each bounded task receives a fresh shadow context and returns a bounded, reviewable result. The dispatch/runtime implementation remains an open design question.

The proposal is experimental. No performance, novelty, cache-hit, or secure-isolation claim is made without evidence.
