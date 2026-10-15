# Native Governance Migration Check

This directory records an executed conformance audit, not a substantive research
comparison or a Lean proof. Earlier native/contract evidence in the parent
directory retains its original source identity and scope.

- `migration_validation.json`: complete scenario, matched seeds, per-trajectory
  results, effective native/reference backend identities, source fingerprints,
  environment and audit-script hash. All 480 matched rounds agree, excluding
  only governance provenance.
- `prolog_response.json`: native response to
  `data/governance/v1/example_request.json`, checked independently and compared
  against the Python producer. The example is authored, not an empirical event.
- `checks.json`: actual regression/native test counts, environments and report
  hashes; Lean was not rerun and hosted CI was not observed.

Reproduce from the checkout with the pinned native backend available:

```bash
python -m pytest -q
python -m pytest -q -m prolog tests/integration -p no:cacheprovider
python experiments/check_governance_migration.py --output results/migration
```

The audit uses four rules, seeds 1/42/123, eight generated residents and 40 rounds.
It keeps institutional checks enabled in both implementations. Separate native
tests cover extinct electorates, blocked policies, precision boundaries, complete
certificates and parallel execution. Finite matched coverage is not a general
equivalence proof. Ordinary simulation exports check witnesses before effects
but do not retain the full per-round certificates.
