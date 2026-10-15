# Reproducibility Guide

Current physical mechanics use `stock-budgeted-v2`; see
[physical accounting](physical_accounting.md). Old numerical results must be
regenerated, even when random event keys and scenario filenames match.

Run from the repository root after creating/activating a virtual environment.
See the [README installation steps](../README.md#install-and-try-it).

Recommended environment:

- Python 3.11-3.13 as the recommended range; the dated review also passed on 3.14.3;
- editable install with development dependencies;
- SWI-Prolog 9.2.9 and PySwip 0.3.3 for required governance integration;
- Lean 4.19.0 via elan for the separately checked formal core.

Commands:

```bash
python -m pip install -e ".[dev]"
python -m pytest
pcds compare --steps 30 --runs 20 --output results/comparison.csv
pcds suite --sensitivity --workers 4 --steps 40 --runs 100 --seed 42 --output-dir results/research_review_2026-10-14
```

Every simulation accepts a base seed. `compare` records the concrete seed used
for each run, and `suite` writes metadata alongside the raw data.

The `event-keyed-v1` randomness scheme separates external shocks, background
health damage, policy effects, private assessments, and bootstrap inference.
Outputs generated before this scheme use different physical trajectories even
with the same seed and must be regenerated. An unseeded Python run records its
resolved seed in every round's `simulation_seed` field for later replay.

For identical scenario/population and seed, `environment_trace_digest` and
`shock_count` must match across rules. The digest covers shock uniforms, shock
occurrences, and potential background health damage for every original agent.
The suite validates these matches before writing results. Raw differences
and analysis metadata make the bootstrap intervals independently auditable;
bit-for-bit reproduction also requires the same Python/NumPy versions.
Suite metadata records Python, NumPy, NetworkX, Polars, and Pydantic versions.

The `separate-outcomes-v1` metric schema changes welfare and assigns zero health
to deaths when computing population dispersion. Regenerate previous metric
exports; do not pool values from different schemas. Conditional outcomes use
blank CSV cells and explicit run/pair counts. Welfare weights, resource
references, and prespecified sensitivity profiles are recorded in suite metadata.


To reproduce the dated 640-run review configuration rather than the default
100-replication suite:

```bash
pcds suite --runs 20 --steps 40 --seed 42 --output-dir results/review_snapshot
```

This runs four mechanisms in eight conditions: 20 * 4 * 8 = 640 trajectories,
with 40 rounds in each. Retain the generated metadata and raw files with any
shared report. Generated result directories are ignored by Git; cloning the
repository does not supply a previously generated local report.

Commands verify Python behavior in the source checkout. They do not test a
standalone wheel's data-file discovery. The default test selection excludes
native checks; run the separate [Prolog and Lean commands](rules.md#pinned-toolchains-and-separate-checks)
to establish their coverage. The default Prolog rules path is resolved from the
source checkout, and the Lean toolchain uses an exact release selector. See the
[review checklist](artifact_checklist.md) for release work still required.

`--require-prolog` is available on `run`, `compare`, and `suite`. It requires the
reference runtime versions and rejects fallback. `--use-prolog` retains optional
loading with a recorded fallback reason. All new observations/CSV exports record
the effective governance backend, and suite metadata records observed identities
alongside reference versions. Pairing rejects inconsistent governance identities
within a condition. Backend choice is part of the experimental treatment:
enabling institutional policy checks can change outcomes compared with the
historical Python-only study, even under identical seeds.

The Python-only mechanics and random-event keys are unchanged by this integration
revision. Historical outcomes remain tied to their recorded revision; their
metadata must not be rewritten to claim newly tested native coverage. New source
hashes include the toolchain declarations and Lean sources. Native test results
describe their explicitly executed environments, not every operating system.

## Current Reviewer Snapshot

The additive [governance contract](governance_contract.md) can be reproduced
independently of simulation seeds: `pcds govern` consumes the published JSON
request and `pcds check-governance` checks its bound response. Its authored
examples are separate from measured study outputs. These commands currently
use the Python reference implementation; they do not request Prolog or Lean.

The expanded [study protocol](study_protocol.md) uses 100 replications, 14
conditions, four rules, and 40 cycles (5,600 trajectories). The original eight
conditions remain the default when `--sensitivity` is omitted. The
[current-results page](current_results.md) links a retained evidence snapshot.

```bash
python experiments/prepare_review_snapshot.py results/research_review_2026-10-14 docs/evidence/2026-10-14 --holdout results/research_holdout_2026-10-14
```

The packaging script checks validation, row counts and current source hashes;
retains raw outcomes, effects, metadata, figures and checksums; and compresses
per-seed differences without removing rows. `environment_requirements.txt`
records installed project/test dependencies for the checked Windows/Python 3.14
environment. It is not a portable lockfile or evidence of a clean-room install.
Full configurations and actual local source identities accompany the artifacts;
an unchanged Git commit alone would not identify uncommitted changes.

`--workers 4` runs independent conditions in separate processes. The default is
1; tests compare sequential and parallel values and condition ordering. Workers
share no mutable simulation state and retain the same seed schedule. Metadata
records the worker count; CSV outputs do not depend on completion order.

The separate baseline seed-block check can be reproduced numerically with:

```bash
pcds compare --runs 20 --steps 40 --seed 10042 --output results/research_holdout_2026-10-14/holdout_raw.csv
```

The retained snapshot also contains that block's effects, paired observations,
and recorded configuration. It is analyzed separately from the main 100-seed
conditions, with its own bootstrap seed 10042. Twenty seeds provide limited
precision; a different seed block is not external empirical validation.
