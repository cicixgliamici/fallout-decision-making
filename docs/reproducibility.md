# Reproducibility Guide

Recommended environment:

- Python 3.11-3.13;
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
