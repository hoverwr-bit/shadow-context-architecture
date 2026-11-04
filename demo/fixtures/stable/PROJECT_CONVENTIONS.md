# Stable Project Conventions

- The cockpit is a structured user-facing workspace, not an Agent or orchestrator.
- Versioned project files are the durable source of project state.
- A new bounded task starts with a fresh Shadow execution context.
- Never import a previous Shadow transcript or tool trace unless explicitly supplied as an authorized artifact.
- Proposed project changes require explicit acceptance.
