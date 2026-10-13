import ast

import polars as pl
import pytest
from typer.testing import CliRunner

from pcds.cli import app
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import compare_rules, run_simulation


def test_cli_run_smoke():
    result = CliRunner().invoke(app, ["run", "--steps", "1", "--agents", "5", "--seed", "1"])
    assert result.exit_code == 0
    assert "Survival rate" in result.output


def test_cli_compare_smoke(tmp_path):
    output = tmp_path / "comparison.csv"
    result = CliRunner().invoke(
        app,
        ["compare", "--steps", "1", "--runs", "1", "--agents", "5", "--output", str(output)],
    )
    assert result.exit_code == 0
    assert output.exists()
    effects = pl.read_csv(tmp_path / "comparison_effects_vs_majority.csv")
    assert effects["n_pairs"].unique().to_list() == [1]
    assert effects["ci95_lower"].null_count() == effects.height
    assert (tmp_path / "comparison_paired_differences.csv").exists()
    assert "unavailable with fewer than two seed pairs" in result.output


@pytest.mark.parametrize("population", [5, 40])
def test_cli_run_uses_requested_population(population):
    result = CliRunner().invoke(
        app, ["run", "--steps", "1", "--agents", str(population), "--seed", "1"]
    )
    assert result.exit_code == 0
    resources = ast.literal_eval(result.output.split("Resources: ", 1)[1].strip())
    expected = run_simulation("majority", steps=1, n_agents=population, seed=1)
    assert resources == expected[-1].resources


def test_cli_compare_uses_requested_population(tmp_path):
    output = tmp_path / "comparison.csv"
    result = CliRunner().invoke(
        app,
        [
            "compare",
            "--steps",
            "1",
            "--runs",
            "1",
            "--agents",
            "5",
            "--seed",
            "1",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert pl.read_csv(output).equals(compare_rules(runs=1, steps=1, n_agents=5, seed=1))


def test_cli_preserves_custom_scenario_population(tmp_path):
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 7
    path = tmp_path / "scenario.json"
    path.write_text(scenario.model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["run", "--steps", "1", "--scenario", str(path)])
    assert result.exit_code == 0
    resources = ast.literal_eval(result.output.split("Resources: ", 1)[1].strip())
    assert (
        resources == run_simulation("majority", steps=1, seed=42, scenario=scenario)[-1].resources
    )


@pytest.mark.parametrize("command", ["run", "compare"])
def test_cli_rejects_non_positive_population(command):
    result = CliRunner().invoke(app, [command, "--agents", "0"])
    assert result.exit_code == 2
