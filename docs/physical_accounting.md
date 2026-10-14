# Physical Accounting

Implemented on **2026-10-14**, physics schema `stock-budgeted-v2`.
These are explicit abstract stock budgets, not engineering or clinical estimates.

## One Cycle

1. If any resident is alive, replenish energy before private assessments and voting.
2. Update rankings, resolve ballots, and apply optional institutional checks.
3. Record the selected policy, satisfaction, and ballot ownership.
4. Check every required physical input. An unaffordable policy has no policy
   effects: no expenditure, production, healing, or policy injuries. The selection
   remains visible, with `policy_executed=false` and a `policy_block_reason`.
   There is no automatic replacement with a cheaper policy.
5. For an affordable policy, debit energy and apply resource deltas. Negative
   resource deltas must be fully covered by stocks before the policy begins;
   positive production cannot finance those operating inputs.
6. Treat eligible patients using the post-production medicine stock, then apply
   policy injuries. Routine consumption, shortage checks, shocks, and health
   damage follow in their existing order.

If no residents are alive, neither generation nor policy execution occurs. The
farming recording default and fixed observation horizon remain; external losses
may still be recorded. Sanctioned living residents remain physical residents:
exclusion from voting does not exclude them from care or consumption.

## Configurable Parameters

All three fields live under `parameters` in scenario JSON and have these defaults:

| Field | Default | Meaning |
| --- | ---: | --- |
| `energy_replenishment` | 2 | Community-wide routine energy generation per inhabited cycle; nonnegative. |
| `energy_capacity` | 50 | Ceiling for new generation; nonnegative. |
| `treatment_medicine_per_health` | 1 | Medical units per summed health point actually restored; strictly positive. |

Generation is `min(energy_replenishment, max(0, energy_capacity - current_energy))`.
An authored initial reserve above capacity is preserved, with no new generation
until it falls below capacity. A zero generation rate models a finite battery;
a zero capacity disables generation. Generation is independent of votes and
population size while inhabited; no fuel, equipment degradation, or maintenance
is implied. Baseline policy costs remain 2 energy, or 4 for defense, so repeated
defense can still exhaust operating reserves.

## Medical Allocation

A living resident strictly below health 0.75 requests the existing keyed random
boost, uniform between 0.5 and 1.5 times the selected policy's `health_boost`.
First cap each request by the patient's remaining health capacity. Let `H` be
the sum of those capped requests, `M` the post-production medical stock, and `c`
the medicine cost per health point. If `H > 0`, the common coverage is:

```text
coverage = min(1, M / (c * H))
actual recovery(patient) = capped request(patient) * coverage
medicine spent = c * sum(actual recovery)
```

Requests are evaluated in name order for reproducible floating-point summation.
Every patient receives the same fraction of their request, independent of input
ordering, role, vote, or sanctions. Dead residents and residents at or above 0.75
receive no treatment. Zero stock after production means no healing. Unused
stock remains available for routine consumption. Routine medicine consumption
represents separate background use, not a second charge for the same treatment.

The baseline conversion of one medicine unit per full summed health point keeps
the stock and health units explicit without imposing an assumed dose size. It
is a modeling parameter for sensitivity analysis, not clinical calibration.

## What Residents Estimate

Adaptive assessments check required inputs using private noisy stock estimates.
An apparently unaffordable policy scores -1 plus its stable priority term.
Estimated healing is bounded by estimated post-production medical stock divided
by conversion cost and living population; estimated treatment spending reduces
the medicine reserve benefit. These are aggregate expectations, not previews of
patient-level random draws. The physical gate always uses actual stocks, so a
misinformed or fixed-preference electorate can still choose a blocked policy.

Satisfaction measures congruence with the selected policy, even when it fails to
execute. Read execution status and `blocked_policy_count` alongside satisfaction,
survival, and health; agreement with a vote does not establish successful delivery.

## Run a Small Accounting Example

The committed [demonstration scenario](../data/scenarios/accounting_demo.json)
contains two injured residents with fixed medical priorities. It isolates stock
accounting by disabling shocks, background health loss, and medicine-shortage
damage; it is not a research baseline.

```bash
pcds run --scenario data/scenarios/accounting_demo.json --steps 2 --seed 42 --report results/accounting_demo/report.txt --event-log results/accounting_demo/events.json
```

The generated report contains these facts:

```text
CYCLE 0001 / simulation step 0
Routine power: energy +1.000.
Policy not executed: insufficient_energy.

CYCLE 0002 / simulation step 1
Routine power: energy +1.000.
Policy effects: energy -2.000; medicine +0.020.
Treatment supplies: medicine -0.020.
Treatment: 2 residents; total health change +0.020.
```

At the end, both residents survive, summed health has increased from 0.60 to
0.62, and energy and medicine stocks are zero. Event JSON retains unrounded
transactions, patient recovery, and the common treatment coverage fraction.

## Evidence and Compatibility

[Accounting tests](../tests/test_accounting.py) check exact-cost boundaries,
atomic failure across all policies and resource inputs, capacity, zero stock,
health caps, order-independent rationing, replayable blocked/recovered execution,
assessment limits, finite parameters, and rejection of mixed physics versions.
[Resource-budget tests](../tests/test_resource_balance.py) execute a 40-cycle
no-shock schedule with the baseline initial energy reserve, replenishment,
medical spending, and the real affordability gate; all 40 residents survive.
This is finite-horizon feasibility under a prescribed schedule, not a guarantee
that voters discover it or that shocks can be survived indefinitely.

The Python API and CLI commands remain available, and old scenario files load
using the new defaults. Archived legacy/low-hazard scenarios preserve their
budget and hazard contrasts, but now explicitly use the new accounting fields.
They do not reproduce the former engine's outcomes.

Raw comparison rows, suite metadata, and event exports identify the new physics
schema. Event schema is now `simulation-events-v2`; round fields add execution
status and failure reason. Raw comparisons add `blocked_policy_count` for
unaffordable actions and `inactive_cycle_count` for post-extinction cycles,
which are not failed attempts to execute an action.
Random event keys and metric formulas are unchanged. **Regenerate previous
numerical outputs**; do not pool them with the new results. Historical files
without a physics tag must remain separate; pairing checks do not establish
full scenario equivalence. Use the same code revision and recorded configuration
for reproduction. Historical calibration figures in the status/resource pages
remain explicitly dated and are not new performance targets.
