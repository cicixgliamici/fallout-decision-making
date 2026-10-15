# Documentation for Users and Reviewers

This directory explains the runnable project, its assumptions, and its evidence.
Operational instructions for AI coding agents live separately in
[AGENTS.md](../AGENTS.md). The narrative design lives in [Setting.md](../Setting.md).

## Choose a Reading Path

| Audience | Read in this order | Purpose |
| --- | --- | --- |
| New user | [Walkthrough](walkthrough.md), [event reports](event_reports.md), [reproducibility](reproducibility.md) | Understand a run, generate a report, reproduce comparisons. |
| Reviewer or admissions board | [Current results](current_results.md), [research basis](research_basis.md), [presentation guide](presentation_guide.md), [project status](project_status.md), [limitations](limitations.md) | Assess the contribution, evidence, and remaining work. |
| Technical reader | [Model specification](model_specification.md), [study protocol](study_protocol.md), [Code guide](code_guide.md), [model](model.md), [methods](methods.md), [metrics](metrics.md) | Follow execution and inspect assumptions and measurements. |
| Contributor | [Code guide](code_guide.md), [context architecture](context_architecture.md), [roadmap](roadmap.md) | Understand boundaries and proposed extensions. |

## Reference Map

| Topic | Documents |
| --- | --- |
| Experiment design and outputs | [Research question](research_question.md), [methods](methods.md), [experiments](experiments.md), [reproducibility](reproducibility.md) |
| Physical model and measurements | [Model](model.md), [resource balance](resource_balance.md), [physical accounting](physical_accounting.md), [metrics](metrics.md), [glossary](glossary.md) |
| Vault setting and factual narration | [Protocol](vault_protocol.md), [policy dictionary](policy_dictionary.md), [event reports](event_reports.md), [context architecture](context_architecture.md) |
| Governance boundaries | [Prolog rules and scope](rules.md), [versioned governance contract](governance_contract.md) |
| Review and release | [Project status](project_status.md), [limitations](limitations.md), [artifact checklist](artifact_checklist.md), [presentation guide](presentation_guide.md) |
| Research argument and assumptions | [Research basis and bibliography](research_basis.md), [ODD model specification](model_specification.md), [study protocol](study_protocol.md) |
| Latest evidence | [Current results and discussion](current_results.md) |
| Future work | [Roadmap](roadmap.md) |

## How to Read Status Claims

- Implemented behavior is grounded in source code and tests.
- Dated checks describe that environment and configuration only. Historical
  calibration results are not new experiments or general probability estimates.
- Proposed features belong in the roadmap and setting design; neither establishes
  that a mechanic is executable.
- Generated files under `results/` are ignored by Git. Keep raw outputs and
  metadata with shared reports; a path in documentation does not archive evidence.

The project currently provides a research simulator and deterministic reports.
A playable terminal, dynamic trust, factions with behavioral effects, and specific
infrastructure failures remain proposed.
