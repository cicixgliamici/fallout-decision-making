# Instructions for AI Coding Agents

This file contains operational guidance for coding assistants. Human readers
should start with [README.md](README.md) and the [documentation index](docs/README.md).
Implementation status belongs in [project status](docs/project_status.md), not here.

## Code and communication conventions

- Write code and code comments in English.
- Prefer short functions with clear responsibilities.
- Use names that future readers can understand.
- Explain non-obvious decisions and their rationale in comments.
- Keep the implementation understandable for reviewers and admissions boards.

## Project guidance

> **Read this section as project guidance, not as permission to claim features that do not exist.** Repository code and tests determine implementation status. The project owner decides scope and priorities.

### Mission

Help build a **technically credible, narratively compelling, reproducible governance experiment**. Protect the simulation's scientific integrity while giving the post-crisis setting recognizable personality. Avoid generic, bloated “AI project” prose and unrelated features.

### Before editing code

1. Read `README.md`, `docs/project_status.md`, `docs/model.md`, `docs/methods.md`, `docs/metrics.md`, and `docs/limitations.md` when relevant to the task.
2. Inspect the actual modules and tests involved; do not infer behavior from folder names or this setting document.
3. State whether a requested feature is **implemented**, **partially implemented**, or **proposed**.
4. Identify the smallest coherent change and the invariant(s) it might affect.
5. Preserve backwards compatibility where practical, particularly scenario input, `pcds` commands, seed behavior, and exported research data. Explain intentional breaking changes.

### Implementation rules

- Keep the **simulation engine independent from the narrative/TUI layer**. No terminal output, flavor selection, or text generation may change policy selection, update order, or simulation RNG streams.
- Prefer scenario-configured effects and typed, validated data over scattered special cases and magic constants.
- Maintain a strict distinction between **simulated facts**, **fictional narration**, **model assumptions**, and **real-world claims**.
- For stochastic extensions, introduce named/keyed random events; test repeatability and cross-rule comparability. Never alter existing event keys casually.
- For every new mechanic, define when it updates, what it reads/writes, who can observe it, and how it is measured. Add boundary tests and a minimal end-to-end test.
- Avoid silently changing `majority` semantics: it is currently *plurality*. Rename only with an explicit migration/alias plan.
- Do not describe the current Lean proofs as verification of Python. Extend formal work only with precise statements, meaningful proof obligations, and separately runnable checks.
- Do not claim real SWI-Prolog behavior has been tested unless it has actually run against the intended backend.
- Make research configurations and their outputs reproducible; export configurations, seeds, effect estimates, and appropriate coverage information.
- Keep documentation candid. If an experiment fails, a feature is incomplete, or a design assumption is arbitrary, say so.

### Narrative-writing rules

- **Show concrete stakes:** who needs what, what could go wrong, whose priorities conflict.
- **Write with restraint:** concise incident reports, evocative details, no endless dystopian monologues.
- **Avoid caricature:** no faction is always correct; experts can err; popular choices can be wise; delegation can both help and concentrate power.
- **Keep the timeline consistent:** casualties cannot speak later without an explicitly modeled reason; exhausted reserves cannot magically recover; events must reflect the recorded state.
- **Use original lore:** Vault 47 is our proposed setting, not a canonical Fallout Vault. Avoid copying recognizable characters, dialogue, or protected assets.
- **Do not fabricate explanatory causality:** a narrative may state that a decision preceded a loss, but it must not assert that the voting rule caused the loss without appropriate comparative evidence.

### Deliverables expected from an agent

For any nontrivial change, provide:

1. **Intent:** why this change serves the Vault narrative *and/or* the research question.
2. **Scope:** files changed, mechanics added, and existing interfaces preserved or changed.
3. **Evidence:** tests run, results observed, and explicit untested parts.
4. **Research implications:** whether previous experiment outputs must be regenerated or comparisons are no longer directly compatible.
5. **Reader-facing artifact:** a small scenario, terminal example, trace, or figure demonstrating the feature when feasible.

Do not write “production-ready,” “formally verified,” or “scientifically proven” unless the claim is narrowly defined and supported by evidence.

### Acceptance checklist for a narrative feature

- [ ] It serves a precise story or analytical purpose.
- [ ] It is clearly marked as planned or implemented in documentation.
- [ ] Its state transitions and effects are explicit (or it is labeled flavor-only).
- [ ] It cannot influence simulation randomness merely by being displayed.
- [ ] It has tests for normal and edge cases.
- [ ] It produces no impossible timeline or unsupported retrospective explanation.
- [ ] It can be disabled without changing numeric simulation outputs.

### Acceptance checklist for a research feature

- [ ] The hypothesis or question is stated without assuming a winner.
- [ ] The mechanism is defined precisely enough to reproduce.
- [ ] Test cases cover correctness, boundary conditions, and invariants.
- [ ] Experiment inputs, seeds, and environment are recorded.
- [ ] Comparisons use matched conditions when appropriate.
- [ ] Material outcomes and democratic/representation outcomes are not conflated.
- [ ] Limitations and incomplete validation are disclosed.

