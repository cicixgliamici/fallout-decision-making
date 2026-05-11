from __future__ import annotations

from pathlib import Path

import typer
import polars as pl

from pcds.simulation import compare_rules, run_simulation

app = typer.Typer(help="Post-Crisis Collective Decision Simulator")


@app.command()
def run(
    rule: str = typer.Option("majority", help="Voting rule to use."),
    steps: int = typer.Option(25, help="Number of simulation steps."),
    agents: int = typer.Option(40, help="Number of agents."),
    seed: int = typer.Option(42, help="Random seed."),
) -> None:
    """Run a single simulation."""
    results = run_simulation(rule=rule, steps=steps, n_agents=agents, seed=seed)
    last = results[-1]
    typer.echo(f"Rule: {rule}")
    typer.echo(f"Selected policy at final step: {last.selected_policy.value}")
    typer.echo(f"Survival rate: {last.survival_rate:.3f}")
    typer.echo(f"Welfare: {last.welfare:.3f}")
    typer.echo(f"Inequality: {last.inequality:.3f}")
    typer.echo(f"Resources: {last.resources}")


@app.command()
def compare(
    steps: int = typer.Option(30, help="Number of simulation steps."),
    runs: int = typer.Option(20, help="Number of runs per rule."),
    agents: int = typer.Option(40, help="Number of agents."),
    seed: int = typer.Option(42, help="Random seed."),
    output: Path = typer.Option(Path("results.csv"), help="CSV output path."),
) -> None:
    """Compare the baseline voting rules."""
    df = compare_rules(runs=runs, steps=steps, n_agents=agents, seed=seed)
    df.write_csv(output)
    summary = df.group_by("rule").agg(
        [
            pl.col("final_survival_rate").mean().alias("mean_survival"),
            pl.col("final_welfare").mean().alias("mean_welfare"),
            pl.col("final_inequality").mean().alias("mean_inequality"),
        ]
    )
    typer.echo(summary)
    typer.echo(f"Saved results to {output}")

if __name__ == "__main__":
    app()
