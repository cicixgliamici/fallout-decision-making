# Governance Rules and Optional Layers

This page distinguishes institutional permission from physical consequences.
A policy can be permitted by a rule while the physical model still has unrealistic
resource constraints. The [walkthrough](walkthrough.md) explains where these
checks occur in a round.

The [governance contract](governance_contract.md) now specifies the complete
current decision procedure as versioned input/output/certificate data. Its
Python reference and pure Prolog producer preserve existing tie-breaking, cycles,
depth limits, and post-election permissions. An independent Python checker checks
every native witness before policy effects. Optional
[Lean certification](lean_certification.md) now proves concrete translated
conformance and selected general invariants.

## What the Python Simulator Uses

Without `--use-prolog` or `--require-prolog`, eligibility is checked in Python: members must be alive
and unsanctioned. Policy-admissibility checks from the optional bridge are not
applied. Python remains the voting resolver in this mode.

With `--use-prolog`, [PrologRuleEngine](../src/pcds/prolog_rules.py) loads the
native backend. The simulator sends an ordered contract snapshot to the pure
[decision module](../rules/governance_decision.pl), which computes eligibility,
delegation, tally, policy permission and a complete witness. If SWI-Prolog,
PySwip, or the rule file cannot be loaded,
the bridge sets `available` to false and uses its Python fallback. Enabling the
option therefore does not prove the real Prolog engine was used. The effective
backend, mode, versions, rule-file hash, and any fallback reason are now recorded
in round observations, event logs, comparison CSVs, and suite metadata.

`--require-prolog` implies enabled checks and requires the reference SWI-Prolog
and PySwip versions. Missing libraries, mismatched versions, missing/malformed
rule files, and initialization failures raise an explicit error. CLI commands
exit unsuccessfully without writing successful result artifacts. Runtime query
errors also stop the run; they never switch a running experiment to Python.

| Request | Effective checks | Recorded backend |
| --- | --- | --- |
| No Prolog flag | Python eligibility only; no institutional policy filter | `python`, mode `disabled` |
| `--use-prolog`, loaded successfully | Real Prolog complete governance decision | `swipl`, mode `optional` |
| `--use-prolog`, loading fails | Python eligibility and mirrored policy thresholds | `python_fallback`, mode `optional`, with reason |
| `--require-prolog` | Pinned real backend, or an explicit error | `swipl`, mode `required` |

Mode identifies institutional checks. The separate `resolver` field identifies
the actual voting producer: `prolog` for a loaded backend by default, `python`
otherwise. Select `--governance-resolver python_reference` to keep Python voting
under the same Prolog checks for migration comparisons. A successfully loaded optional backend
can have a different version; its actual version is recorded, and it is not a
pinned research execution.

## Current Policy Permission

| Policy | Requirement in the optional rule layer |
| --- | --- |
| Farming | Always allowed. |
| Medicine | Always allowed. |
| Defense | Energy at least 2. |
| Exploration | Energy at least 2 and security at least 15. |

The thresholds are institutional assumptions, not a complete affordability
check. For example, default defense costs 4 energy units despite its permission
threshold of 2. The physical engine independently requires all upfront inputs,
so a permitted defense action with only 2 energy is selected but blocked.
The fallback mirrors these permission thresholds; separate real-engine tests
compare both implementations at and immediately below their boundaries.

If a chosen policy is prohibited, the simulator takes the first allowed policy
in declaration order. Under the default rules this is farming. The fallback is
simple and deterministic, not an optimization of community outcomes.

## Delegation and Transport

[governance_decision.pl](../rules/governance_decision.pl) owns ordered expert
selection, single-hop and liquid paths, original-voter cycle fallback, the
three-hop budget, contributions and deterministic tally. It compares trust
fractions by integer cross products. Both implementations treat elders as
medicine specialists. [governance.pl](../rules/governance.pl) imports this
expertise mapping; its legacy `can_delegate/3` remains available but is not the
complete resolver. The Python reference is retained temporarily for comparison.

The native decision relation reads only the supplied snapshot, without dynamic
world facts, physical effects or random draws. Native dictionaries avoid a JSON
library dependency in SWI-Prolog. A response must be unique and pass independent
contract checking; a bad response stops the run before physical effects.

The bridge quotes names as Prolog atoms and escapes quotes/backslashes, keeping
`a-b` and `a_b` distinct. Synchronization clears facts at their declared arities
before loading a new world. Resource values retain Python float precision;
rounding them for transport could change decisions at permission thresholds.
PySwip uses a process-wide interpreter, so simultaneous worlds require separate
processes. The suite's existing process workers satisfy this constraint; this
bridge does not support interleaved independent worlds in the same process.
Workers explicitly use spawn so Unix processes do not inherit an initialized
native interpreter from the parent.

## Pinned Toolchains and Separate Checks

[toolchains.toml](../toolchains.toml) declares SWI-Prolog **9.2.9**, PySwip
**0.3.3**, and Lean **4.19.0** as reference versions. These are deliberate
reproducibility targets, not claims about the latest releases. PySwip is pinned
in both Python dependency declarations; Lean's selector is an exact release.
SWI-Prolog is a native prerequisite and must be installed separately.

Install SWI-Prolog from the [official versioned downloads](https://www.swi-prolog.org/download/stable?show=all).
The [official container](https://www.swi-prolog.org/Docker.md) version
`swipl:9.2.9` is used by the Prolog CI job, with its image index digest fixed.
Ensure the executable and shared
library refer to the same installation. PySwip can use `SWI_HOME_DIR` and
`LIBSWIPL_PATH` when library discovery needs an explicit location.

Run each check from the repository root:

```bash
python -m pytest -q
python -m pytest -q -m prolog tests/integration --junitxml=results/prolog-tests.xml
python -m pytest -q -m lean tests/integration --junitxml=results/lean-tests.xml
```

The default selection excludes native tests. Explicit Prolog/Lean selections
fail if their prerequisites are absent; they do not silently skip. The
[CI workflow](../.github/workflows/checks.yml) runs three independent jobs with
separate test reports. A configured workflow is not evidence of a completed
hosted run; local results are recorded in [project status](project_status.md).

The Prolog checks use the actual bridge and interpreter: eligibility combinations,
threshold boundaries, stale-fact cleanup, distinct/quoted identities, invalid
files, deterministic replay, CLI exports, suite metadata, and process-worker
consistency, complete delegation certificates and matched full trajectories.
Finite test coverage does not establish equivalence for every valid input.

Example strict research execution:

```bash
pcds run --require-prolog --steps 3 --agents 5 --seed 42 --event-log results/prolog-smoke.json
pcds compare --require-prolog --runs 2 --steps 3 --agents 5 --output results/prolog-comparison.csv
pcds suite --require-prolog --runs 2 --steps 3 --output-dir results/prolog-suite
```

These are integration demonstrations, not sufficiently replicated research
results. CSV columns beginning `governance_` identify the actual treatment.
Pairing rejects mixed modes, backends, versions, or rule hashes within a
condition, including resolver/hash/contract identity, even when external random
draws match. Fully historical tables remain readable but do not establish native
voting coverage. Partial resolver identities are rejected.

The [2026-10-15 integration record](evidence/2026-10-15/native_integration.json)
identifies the actually checked environments. A
[three-round trace](evidence/2026-10-15/prolog_smoke.json) retains the loaded
backend, full scenario, seed, events, and representative ownership. This small
run demonstrates the integration; it is not a new research comparison.

## Lean's Different Role

The [Lean governance model](../formal/lean/Wasteland/Governance.lean) now computes
contract-v1 decisions independently. It proves ballot count/coverage, bounded
paths, cycle fallback, score-winner maximality and selected-policy permission.
`pcds certify-governance` translates one JSON request/witness pair into a
kernel-checked concrete conformance proof. The older small definitions remain
available. See [the exact scope](lean_certification.md), including assumptions
on next-hop closure, unique identities and the trusted JSON/literal adapter.
The Lean toolchain is optional for simulation and pinned to
`leanprover/lean4:v4.19.0`. The separate integration check verifies the selected
version and explicitly runs `lake build Wasteland` against the actual sources.
The library is also now a default target. Concrete certificates connect external
witnesses to Lean's computation; they do not prove universal equivalence of
Python/Prolog implementations, physical transitions, or empirical validity.
