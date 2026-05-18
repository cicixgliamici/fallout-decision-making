from __future__ import annotations

from pathlib import Path

import polars as pl
import typer

from pcds.experiments import run_experiment_suite
from pcds.scenarios import default_scenario_path
from pcds.simulation import compare_rules, run_simulation

app = typer.Typer(help="Post-Crisis Collective Decision Simulator")


@app.command()
def run(
    rule: str = typer.Option("majority", help="Voting rule to use."),
    steps: int = typer.Option(25, help="Number of simulation steps."),
    agents: int = typer.Option(40, help="Number of agents."),
    seed: int = typer.Option(42, help="Random seed."),
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    use_prolog: bool = typer.Option(False, help="Use SWI-Prolog governance rules when available."),
) -> None:
    """Run a single simulation."""
    results = run_simulation(
        rule=rule,
        steps=steps,
        n_agents=agents,
        seed=seed,
        scenario=scenario,
        use_prolog=use_prolog,
    )
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
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    output: Path = typer.Option(Path("results/comparison.csv"), help="CSV output path."),
) -> None:
    """Compare the baseline voting rules."""
    output.parent.mkdir(parents=True, exist_ok=True)
    df = compare_rules(runs=runs, steps=steps, n_agents=agents, seed=seed, scenario=scenario)
    df.write_csv(output)
    summary = df.group_by("rule").agg(
        [
            pl.col("final_survival_rate").mean().alias("mean_survival"),
            pl.col("final_welfare").mean().alias("mean_welfare"),
            pl.col("final_inequality").mean().alias("mean_inequality"),
            pl.col("final_resilience").mean().alias("mean_resilience"),
        ]
    )
    typer.echo(summary.write_csv())
    typer.echo(f"Saved results to {output}")


@app.command("suite")
def suite(
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    output_dir: Path = typer.Option(Path("results"), help="Directory for raw data and report."),
    runs: int = typer.Option(100, help="Runs per voting rule and experiment."),
    steps: int = typer.Option(40, help="Steps per run."),
    seed: int = typer.Option(42, help="Base random seed."),
) -> None:
    """Run the reviewer-oriented experiment suite."""
    paths = run_experiment_suite(
        scenario_path=scenario,
        output_dir=output_dir,
        runs=runs,
        steps=steps,
        seed=seed,
    )
    for label, path in paths.items():
        typer.echo(f"{label}: {path}")

if __name__ == "__main__":
    app()
