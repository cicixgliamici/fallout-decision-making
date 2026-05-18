# Experiments

Run a small comparison:

```bash
pcds compare --steps 30 --runs 20 --output results/comparison.csv
```

Run the reviewer-oriented suite:

```bash
pcds suite --steps 40 --runs 100 --output-dir results
```

The suite includes:

- moderate scarcity baseline;
- severe scarcity;
- environmental shocks;
- low-trust and high-trust networks;
- expertise imbalance.

For each condition, the artifact stores raw per-run results, aggregate means,
approximate 95% confidence intervals, metadata, and a Markdown report. The
expected interpretation is comparative: a rule is better supported only when it
improves survival/welfare without hiding large inequality or resilience losses.
