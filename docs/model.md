# Model

The model is a repeated collective choice problem under scarcity.

At each step, living and unsanctioned agents choose one policy through a voting
or delegation mechanism. The selected policy changes resources and health, then
environmental pressure consumes resources and may damage agents.

## Agents

Each agent has:

- role and associated expertise;
- ordinal preferences over policies;
- derived cardinal utility for policies;
- health and survival state;
- risk aversion and cooperation;
- sanction status.

Ordinal preferences drive ballots. Cardinal utility is exposed so later work can
study manipulation, welfare decomposition, and strategic voting without changing
the public model.

## Policies

The current policy set is finite:

- `farming`
- `medicine`
- `defense`
- `exploration`

Policy impacts are scenario parameters. Exploration has stochastic upside and
risk; defense and medicine reduce different failure modes; farming improves
food at a water cost.

## Resources and Shocks

The community tracks food, water, medicine, energy, and security. Scenario files
define initial resources, consumption rates, scarcity thresholds, and optional
environmental shocks.

## Metrics

Primary metrics are:

- survival rate;
- social welfare;
- health inequality;
- resource resilience.

These are summary metrics for comparative mechanism analysis, not direct claims
about real-world welfare.
