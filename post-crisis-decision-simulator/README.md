# Post-Crisis Collective Decision Simulator

A minimal research-oriented MVP for studying **collective decision-making under scarcity**.

The project models a post-crisis community that must repeatedly choose policies such as investing in farming, medicine, defense, or exploration. The goal is not to build a game, but to create a controlled simulation testbed for computational social choice, game theory, delegation, and normative reasoning.

## Core idea

```text
Python  = what happens in the simulation
Prolog  = what is institutionally/normatively allowed
Lean4   = what is formally specified/proved in a tiny core model
```

## MVP 0 features

- Agent-based community model
- Scarce resources: food, water, medicine, energy, security
- Voting mechanisms:
  - majority voting
  - approval voting
  - expert delegation
  - simplified liquid democracy
- Trust/delegation graph using NetworkX
- Normative rules in SWI-Prolog
- Small Lean4 formalization skeleton
- Experiment runner comparing voting mechanisms
- Tests for voting and metrics

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

For Prolog integration, install SWI-Prolog separately. The simulator works even if Prolog is unavailable; it falls back to Python-side rule checks.

## Run baseline experiment

```bash
pcds run --rule majority --steps 20 --seed 42
pcds compare --steps 30 --runs 20
```

Or directly:

```bash
python experiments/compare_voting_rules.py
```

## Research question for MVP 0

> Under scarcity, do delegation-based decision mechanisms improve survival and welfare compared to direct voting?

## Project structure

```text
src/pcds/              Python simulator
rules/                 Prolog normative rules
formal/lean/           Lean4 formal model skeleton
experiments/           Reproducible experiments
docs/                  Research notes
tests/                 Unit tests
data/scenarios/        JSON scenarios
```

## Next steps

- Add Mesa integration for richer agent-based scheduling
- Add coalition formation
- Add strategic manipulation
- Add richer liquid democracy delegation resolution
- Add formal Lean proofs about voting rules and delegation graphs
- Add paper-style experimental report
