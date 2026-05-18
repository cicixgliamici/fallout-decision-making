# Governance Rules

The Prolog layer encodes institutional constraints rather than simulation
dynamics. Python decides what happens after a policy is selected; Prolog decides
whether agents and policies are institutionally admissible.

Current rules cover:

- voting eligibility: alive and not sanctioned;
- topic expertise by role;
- delegation permission through trust and expertise;
- policy admissibility under low security or low energy.

The simulator works without SWI-Prolog. In that case, `pcds.prolog_rules`
provides a Python fallback for the same core policy admissibility rules.
