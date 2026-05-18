# Post-Crisis Collective Decision Simulator

Research artifact for studying **delegation under scarcity** in an original
post-apocalyptic community. The project is intentionally not a game: it is a
small, reproducible testbed for computational social choice, game theory,
normative governance, and lightweight formal specification.

```text
Python  = stochastic multi-agent simulation and experiments
Prolog  = institutional eligibility and policy constraints
Lean 4  = tiny formal core for voting/delegation definitions
```

## Research Question

Under scarcity, do delegation-based decision mechanisms improve survival,
welfare, and equity compared with direct voting?

The baseline compares:

- majority voting
- approval voting
- expert delegation
- simplified liquid democracy

## Install

Recommended Python versions are 3.11-3.13. Python 3.14 may work once all
third-party dependencies publish compatible wheels, but it is not the primary
artifact target.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
python -m pip install -e ".[dev]"
python -m pytest
```

SWI-Prolog is optional. Without it, the simulator uses a Python fallback with the
same core governance semantics.

Lean is optional for the Python artifact. To check the formal core, install
`elan`, configure a Lean 4 toolchain, then run:

```bash
cd formal/lean
lake build
```

## Quickstart

```bash
pcds run --rule majority --steps 20 --seed 42
pcds compare --steps 30 --runs 20 --output results/comparison.csv
pcds suite --runs 100 --steps 40 --output-dir results
```

The suite writes raw results, summaries, metadata, and a Markdown report under
`results/`.

## Project Structure

```text
src/pcds/              simulator, scenarios, metrics, experiments, CLI
rules/                 Prolog governance rules
formal/lean/           Lean 4 formal core
experiments/           standalone plotting/experiment scripts
docs/                  paper-style notes and artifact documentation
tests/                 unit and integration tests
data/scenarios/        JSON scenarios
```

## Artifact Claims

| Claim | Evidence |
| --- | --- |
| Delegation mechanisms can be compared under identical scarcity conditions. | `pcds compare`, seeded runs, `tests/test_simulation.py` |
| Scenario parameters are externalized from code. | `data/scenarios/shelter_alpha.json`, `pcds.scenarios` |
| Governance constraints affect admissible decisions. | `rules/governance.pl`, `pcds.prolog_rules`, fallback tests |
| Formal methods are scoped to a small auditable core. | `formal/lean/Wasteland/*.lean` |

## Limitations

The simulation is intentionally stylized. It supports comparative mechanism
analysis, not prediction of real communities. Strategic manipulation and
coalition formation are future extensions rather than current claims.
