# Reproducibility Guide

Run from the repository root after creating/activating a virtual environment.
See the [README installation steps](../README.md#install-and-try-it).

Recommended environment:

- Python 3.11-3.13 as the recommended range; the dated review also passed on 3.14.3;
- editable install with development dependencies;
- optional SWI-Prolog for governance integration;
- optional Lean 4 via elan for the formal core.

Commands:

```bash
python -m pip install -e ".[dev]"
python -m pytest
pcds compare --steps 30 --runs 20 --output results/comparison.csv
pcds suite --steps 40 --runs 100 --output-dir results
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
standalone wheel's data-file discovery or establish that optional SWI-Prolog
and Lean were checked. The Prolog rules path is also relative to the working
directory, and the Lean toolchain uses a rolling selector. See the
[review checklist](artifact_checklist.md) for release work still required.
