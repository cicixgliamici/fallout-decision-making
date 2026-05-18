# Methods

The artifact compares voting mechanisms with seeded stochastic simulation.

Each run starts from a JSON scenario. Agents are generated or loaded, a directed
trust graph is constructed, and the chosen voting rule selects a policy at each
step. The same random seed schedule is used across mechanisms so differences are
attributable to decision rules rather than uncontrolled setup differences.

The implemented mechanisms are intentionally simple baselines:

- majority: first-place plurality with deterministic tie-breaking;
- approval: top-k approval, default k=2;
- expert delegation: delegate to the most trusted eligible expert for the
  voter's preferred topic;
- liquid democracy: bounded delegation chains with cycle fallback.

Results should be reported with raw data, means, confidence intervals, and the
exact scenario configuration.
