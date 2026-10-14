# Deterministic Reports and Event Records

The engine can now record neutral, ordered events. A separate presentation
module renders those facts as a Vault 47 or neutral report. No text selection
or presentation profile changes a policy, physical effect, or random draw.

## Try the Vault Report

```bash
pcds run --rule expert_delegation --steps 5 --seed 42 --report results/vault47/report.txt --event-log results/vault47/events.json
```

The normal terminal summary remains available. `--report` writes a UTF-8 text
report using the `vault47` profile by default; `--event-log` writes the full
neutral JSON trace. Either option can be used alone. Choose `--profile neutral`
to present the same experiment with neutral labels. Both output paths must be
different. Cycles remain simulation allocations, not days or work shifts.

The following excerpt records a third-cycle shock under the earlier accounting
model (2026-10-13); policy choices can change with the current engine. Run the
[accounting example](physical_accounting.md) for a current blocked-action and
medical-rationing demonstration:

```text
CYCLE 0003 / simulation step 2
Priority: Infirmary support and medical supply preparation [medicine]
Policy effects: energy -2.000; medicine +8.000.
Consumption: food -8.000; water -6.000; medicine -1.600.
Post-consumption shortages: none.
External shock: recorded.
Shock reserve losses: food -12.000; water -10.000; medicine -4.000; security -6.000.
```

This is a historical generated-report excerpt, not an invented incident. A
generic shock is not described as a purifier failure or raider attack. Numerical
text is rounded to three decimals; the JSON preserves full recorded values.

## What an Event Contains

Each `SimulationEvent` has a zero-based step, a sequence number local to that
step, a typed kind, a subject, and a neutral cause. State changes carry before
and after values. Intended changes and numeric details are included where
applicable. Sequence numbers identify actual execution order, not prose order.

| Kind | Recorded fact |
| --- | --- |
| `policy_selected` | Selected ballot policy and electorate size; no-voter defaults have a distinct cause. |
| `policy_override` | Requested policy replaced by the optional institutional checks; subject is the applied policy, cause is the requested policy. |
| `policy_blocked` | Selected action failed its physical input check or has no living residents; no policy effects follow. |
| `resource_change` | Actual before/after reserve values and requested delta; causes include generation, policy, treatment spending, consumption, and shocks. |
| `treatment` | Named living resident's actual healing, capped request, and common budget coverage fraction. |
| `injury` | Named living resident's actual policy injury and sampled loss. |
| `shortage` | Resource value, threshold, and per-resident damage component, checked after consumption and before shock losses. |
| `shock` | Generic external event and configured direct health damage. |
| `health_damage` | Actual health endpoints, requested damage, and shortage/shock/background components. |
| `death` | Living-to-dead transition, final health, and death threshold. |

Resource changes are recorded even when a nonzero requested effect is entirely
blocked by the zero stock floor. Zero requested deltas produce no transaction.
Damage components are nominal amounts; actual loss can be lower when health
reaches zero. Death records indicate a threshold transition, not a uniquely
identified medical cause or an effect of the voting rule.

Routine power generation now precedes assessments and can be the first event
in a cycle. `policy_selected` records the vote; optional overrides precede the
physical input gate. Treatment spending follows production and precedes routine
consumption. No generation or policy execution occurs after extinction.
Treatment precedes
policy injuries; environmental health damage follows consumption, shortage
checks, and shock losses. A shock's stock loss can cause a shortage next cycle;
it does not trigger another shortage check immediately. Already-dead residents
have no subsequent treatment, injury, damage, or death events. External shocks
and stock accounting can still be recorded after extinction because the model
retains a fixed observation horizon.

## Export and Replay

The JSON envelope records `simulation-events-v2`, physics schema
`stock-budgeted-v2`, the existing randomness and metric schemas, and complete
round records, including execution status, votes, and event lists. Numerical
outputs from before this accounting revision must be regenerated.
CLI exports also contain the resolved scenario configuration with any generated
population override and whether optional governance checks were requested.
This flag does not establish which Prolog backend was available; reproducing
optional checks requires the same backend environment.
Timestamps are omitted deliberately so repeated exports
can match byte for byte. Scenario configuration and the recorded root seed
allow a run to be reproduced in the same code/runtime environment.

In Python, recording is opt-in:

```python
from pcds.narrative import PROFILES, export_event_log, render_report
from pcds.simulation import run_simulation

results = run_simulation("majority", steps=5, seed=42, record_events=True)
vault_text = render_report(results, PROFILES["vault47"])
neutral_text = render_report(results, PROFILES["neutral"])
event_json = export_event_log(results)
```

The Python exporter accepts an optional `scenario_configuration` dictionary;
the CLI supplies it automatically. Renderers reject missing event records or
disordered/mixed histories rather than invent missing facts. Existing
`RoundResult` records gain an additive `events` field, empty when recording is
disabled. `compare` and `suite` keep recording disabled and their CSV schema
unchanged. Prior numerical experiment outputs need no regeneration for this
observational change.

## A Reusable Presentation Profile

Save this example as a standalone JSON file and use its path with `--profile`:

```json
{
  "title": "LUNAR COLONY / GOVERNANCE RECORD",
  "introduction": "An isolated colony with finite reserves.",
  "policy_labels": {
    "farming": "Greenhouse and water reclamation",
    "medicine": "Medical support",
    "defense": "Habitat protective readiness",
    "exploration": "External supply survey"
  }
}
```

A profile defines vocabulary only. Missing labels use their engine identifiers.
Physical assumptions belong in the scenario; report amounts come from the
recorded transactions, never hard-coded policy-dictionary values. Profiles
cannot add radiation, named expedition crews, infrastructure states, or an
incident cause that the engine did not record.

Implementation is separated across [events.py](../src/pcds/events.py),
[simulation.py](../src/pcds/simulation.py), and
[narrative.py](../src/pcds/narrative.py). Tests check recording-on/off invariance,
same-seed replay, exact stock/health reconstruction, thresholds and floors,
extinction, institutional overrides, and unchanged exports across profiles.
