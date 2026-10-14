import ast
import json

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


def test_cli_exports_replayable_event_log_and_deterministic_report(tmp_path):
    report = tmp_path / "vault.txt"
    log = tmp_path / "events.json"
    arguments = [
        "run",
        "--steps",
        "3",
        "--agents",
        "5",
        "--seed",
        "42",
        "--report",
        str(report),
        "--event-log",
        str(log),
    ]
    runner = CliRunner()
    result = runner.invoke(app, arguments)
    assert result.exit_code == 0, result.output
    text, data = report.read_bytes(), log.read_bytes()
    payload = json.loads(data)
    assert payload["event_schema"] == "simulation-events-v2"
    assert payload["scenario_configuration"]["agents"] == 5
    assert payload["governance_checks_enabled"] is False
    assert len(payload["rounds"]) == 3
    assert any(e["kind"] == "policy_selected" for e in payload["rounds"][0]["events"])
    assert payload["physics_schema"] == "stock-budgeted-v2"
    assert b"VAULT 47" in text
    assert runner.invoke(app, arguments).exit_code == 0
    assert report.read_bytes() == text and log.read_bytes() == data
    neutral = runner.invoke(app, [*arguments, "--profile", "neutral"])
    assert neutral.exit_code == 0
    assert b"VAULT 47" not in report.read_bytes()
    assert log.read_bytes() == data


def test_cli_event_log_without_report_and_invalid_output_arguments(tmp_path):
    runner = CliRunner()
    log = tmp_path / "events.json"
    result = runner.invoke(app, ["run", "--steps", "1", "--event-log", str(log)])
    assert result.exit_code == 0 and log.exists()
    same_path = runner.invoke(app, ["run", "--report", str(log), "--event-log", str(log)])
    assert same_path.exit_code == 2
    invalid = runner.invoke(
        app,
        ["run", "--report", str(tmp_path / "bad.txt"), "--profile", str(tmp_path / "missing.json")],
    )
    assert invalid.exit_code == 2
    assert not (tmp_path / "bad.txt").exists()


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


def test_cli_suite_forwards_the_optional_sensitivity_panel(monkeypatch, tmp_path):
    received = {}

    def capture_suite(**arguments):
        # Isolate command wiring; actual condition construction is tested separately.
        received.update(arguments)
        return {}

    monkeypatch.setattr("pcds.cli.run_experiment_suite", capture_suite)
    result = CliRunner().invoke(app, ["suite", "--sensitivity", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert received["sensitivity"] is True
    assert received["workers"] == 1
    assert received["output_dir"] == tmp_path
