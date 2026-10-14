"""Expose the research pipeline as small commands: run, compare, and suite.

Printed outcomes and exported coverage help readers inspect more than one aggregate score.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import typer

from pcds.experiments import run_experiment_suite, summarize_rules
from pcds.models import RoundResult
from pcds.narrative import export_event_log, load_profile, render_report
from pcds.paired_analysis import build_paired_differences, summarize_paired_effects
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import compare_rules, run_simulation

app = typer.Typer(help="Post-Crisis Collective Decision Simulator")


@app.command()
def run(
    rule: str = typer.Option("majority", help="Voting rule to use."),
    steps: int = typer.Option(25, help="Number of simulation steps."),
    agents: int | None = typer.Option(
        None, min=1, help="Override synthetic population; defaults to the scenario."
    ),
    seed: int = typer.Option(42, help="Random seed."),
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    use_prolog: bool = typer.Option(False, help="Use SWI-Prolog governance rules when available."),
    report: Path | None = typer.Option(None, help="Write a deterministic text report."),
    event_log: Path | None = typer.Option(None, help="Write a neutral JSON event trace."),
    profile: str = typer.Option("vault47", help="Report profile: vault47, neutral, or JSON path."),
) -> None:
    """Print one trajectory's final material outcomes and decision-time representation."""
    # Resolve presentation before running; an invalid profile must not waste a simulation.
    try:
        narrative_profile = load_profile(profile) if report else None
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error), param_hint="--profile") from error
    if report and event_log and report.resolve() == event_log.resolve():
        raise typer.BadParameter("report and event log must use different paths")
    scenario_configuration = load_scenario(scenario)
    results = run_simulation(
        rule=rule,
        steps=steps,
        n_agents=agents,
        seed=seed,
        scenario=scenario_configuration,
        use_prolog=use_prolog,
        record_events=report is not None or event_log is not None,
    )
    _print_run_summary(results[-1])
    if report:
        _write_artifact(report, render_report(results, narrative_profile))
    if event_log:
        # Preserve the actual synthetic population override in replay metadata.
        if isinstance(scenario_configuration.agents, int):
            scenario_configuration.agents = results[0].initial_population
        _write_artifact(
            event_log,
            export_event_log(
                results,
                scenario_configuration.model_dump(mode="json"),
                governance_checks_enabled=use_prolog,
            ),
        )


def _print_run_summary(last: RoundResult) -> None:
    """Keep the established terminal summary separate from optional artifacts."""
    typer.echo(f"Rule: {last.rule}")
    typer.echo(f"Selected policy at final step: {last.selected_policy.value}")
    typer.echo(f"Policy executed: {last.policy_executed}")
    if last.policy_block_reason:
        typer.echo(f"Policy blocked: {last.policy_block_reason}")
    typer.echo(f"Survival rate: {last.survival_rate:.3f}")
    typer.echo(f"Welfare: {last.welfare:.3f}")
    typer.echo(f"Inequality: {last.inequality:.3f}")
    typer.echo(f"Survivors: {last.survivors}/{last.initial_population}")
    typer.echo(f"Survivor health: {_format_optional(last.survivor_health)}")
    typer.echo(f"Population health: {last.population_health:.3f}")
    typer.echo(f"Decision-time eligible voters: {last.eligible_voters}")
    typer.echo(f"Preference satisfaction: {_format_optional(last.preference_satisfaction)}")
    typer.echo(
        f"Initial preference satisfaction: {_format_optional(last.prior_preference_satisfaction)}"
    )
    typer.echo(f"Delegation concentration: {_format_optional(last.delegation_concentration)}")
    typer.echo(f"Largest ballot share: {_format_optional(last.max_vote_share)}")
    typer.echo(f"Welfare contributions: {last.welfare_components}")
    typer.echo(f"Welfare weight sensitivity: {last.welfare_sensitivity}")
    typer.echo(f"Resources: {last.resources}")


def _write_artifact(path: Path, content: str) -> None:
    """Keep filesystem operations outside both simulation and rendering."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    typer.echo(f"Saved {path}")


@app.command()
def compare(
    steps: int = typer.Option(30, help="Number of simulation steps."),
    runs: int = typer.Option(20, help="Number of runs per rule."),
    agents: int | None = typer.Option(
        None, min=1, help="Override synthetic population; defaults to the scenario."
    ),
    seed: int = typer.Option(42, help="Random seed."),
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    output: Path = typer.Option(Path("results/comparison.csv"), help="CSV output path."),
) -> None:
    """Export matched rule outcomes, per-seed differences, and paired effect intervals."""
    output.parent.mkdir(parents=True, exist_ok=True)
    df = compare_rules(runs=runs, steps=steps, n_agents=agents, seed=seed, scenario=scenario)
    df.write_csv(output)
    paired = build_paired_differences(df.with_columns(pl.lit("comparison").alias("experiment")))
    effects = summarize_paired_effects(paired, seed=seed)
    paired_path = output.with_name(f"{output.stem}_paired_differences.csv")
    effects_path = output.with_name(f"{output.stem}_effects_vs_majority.csv")
    paired.write_csv(paired_path)
    effects.write_csv(effects_path)
    summary = summarize_rules(df)
    typer.echo(summary.write_csv())
    typer.echo(f"Saved results to {output}")
    typer.echo(f"Saved paired differences to {paired_path}")
    typer.echo(f"Saved paired effects and confidence intervals to {effects_path}")
    if runs < 2:
        typer.echo("Paired confidence intervals are unavailable with fewer than two seed pairs.")
    if effects.filter(pl.col("n_undefined_pairs") > 0).height:
        typer.echo(
            "Conditional effects use pairs defined in both rules; inspect the pair coverage columns."
        )


def _format_optional(value: float | None) -> str:
    """Print N/A for an undefined conditional measure rather than a misleading zero."""
    return "N/A" if value is None else f"{value:.3f}"


@app.command("suite")
def suite(
    scenario: Path = typer.Option(default_scenario_path(), help="Scenario JSON path."),
    output_dir: Path = typer.Option(Path("results"), help="Directory for raw data and report."),
    runs: int = typer.Option(100, help="Runs per voting rule and experiment."),
    steps: int = typer.Option(40, help="Steps per run."),
    seed: int = typer.Option(42, help="Base random seed."),
    sensitivity: bool = typer.Option(False, help="Add six physical-assumption sensitivity probes."),
    workers: int = typer.Option(1, min=1, help="Independent worker processes for suite conditions."),
) -> None:
    """Run all predefined conditions and report where their review artifacts were written."""
    paths = run_experiment_suite(
        scenario_path=scenario,
        output_dir=output_dir,
        runs=runs,
        steps=steps,
        seed=seed,
        sensitivity=sensitivity,
        workers=workers,
    )
    for label, path in paths.items():
        typer.echo(f"{label}: {path}")


if __name__ == "__main__":
    app()
