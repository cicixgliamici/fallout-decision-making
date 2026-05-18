# Artifact Checklist

- [x] Installable Python package
- [x] CLI smoke commands
- [x] Seeded reproducible experiments
- [x] Scenario JSON loader
- [x] Unit tests for voting, metrics, simulation, and governance fallback
- [x] Optional Prolog governance layer
- [x] Optional Lean formal core
- [x] Claims-to-evidence table in README
- [x] Reproducibility guide

Smoke test:

```bash
python -m pytest
pcds run --steps 2 --agents 8
pcds compare --steps 2 --runs 2 --agents 8
```
