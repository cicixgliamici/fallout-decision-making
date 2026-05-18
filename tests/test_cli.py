from typer.testing import CliRunner

from pcds.cli import app


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
