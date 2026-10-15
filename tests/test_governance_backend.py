"""Test backend selection and failure handling without requiring a native runtime."""

import json
import sys
from types import SimpleNamespace

import polars as pl
import pytest
from typer.testing import CliRunner

from pcds.cli import app
from pcds.experiments import run_experiment_suite
from pcds.models import GovernanceBackend, Policy
from pcds.paired_analysis import pairing_errors
from pcds.prolog_rules import PrologBackendError, PrologRuleEngine, governance_versions
from pcds.scenarios import default_scenario_path
from pcds.simulation import compare_rules, run_simulation


@pytest.fixture
def missing_runtime(monkeypatch):
    # Inject failure at the native loading boundary, independent of local installs.
    def fail_load(self, rules, required):
        raise ImportError("controlled missing native runtime")

    monkeypatch.setattr(PrologRuleEngine, "_load", fail_load)


def test_disabled_checks_do_not_attempt_prolog_loading(missing_runtime):
    result = run_simulation("majority", steps=1, n_agents=3)[0]
    assert result.governance == GovernanceBackend()


def test_optional_failure_is_explicit_in_rounds_and_csv(missing_runtime):
    result = run_simulation("majority", steps=1, n_agents=3, use_prolog=True)[0]
    assert result.governance.backend == "python_fallback"
    assert "controlled missing" in result.governance.fallback_reason
    raw = compare_rules(runs=1, steps=1, n_agents=3, use_prolog=True)
    assert set(raw["governance_backend"]) == {"python_fallback"}
    assert raw["governance_swipl_version"].null_count() == raw.height


@pytest.mark.parametrize("operation", ["run", "compare", "suite"])
def test_required_backend_fails_before_successful_outputs(missing_runtime, tmp_path, operation):
    with pytest.raises(PrologBackendError, match="Required SWI-Prolog.*controlled missing"):
        if operation == "run":
            run_simulation("majority", steps=1, require_prolog=True)
        elif operation == "compare":
            compare_rules(runs=1, steps=1, require_prolog=True)
        else:
            run_experiment_suite(default_scenario_path(), output_dir=tmp_path / "study",
                                 runs=1, steps=1, require_prolog=True)
    assert not (tmp_path / "study").exists()


@pytest.mark.parametrize("command", ["run", "compare", "suite"])
def test_cli_strict_failure_is_actionable_and_writes_no_results(missing_runtime, tmp_path, command):
    output = tmp_path / "artifact"
    option = {"run": "--event-log", "compare": "--output", "suite": "--output-dir"}[command]
    result = CliRunner().invoke(app, [command, "--require-prolog", option, str(output)])
    assert result.exit_code == 1
    assert "Required SWI-Prolog backend unavailable" in result.output
    assert not output.exists()


def test_optional_cli_event_log_records_the_effective_backend(missing_runtime, tmp_path):
    log = tmp_path / "events.json"
    result = CliRunner().invoke(app, ["run", "--steps", "1", "--agents", "3",
                                    "--use-prolog", "--event-log", str(log)])
    assert result.exit_code == 0
    payload = json.loads(log.read_text(encoding="utf-8"))
    assert payload["governance_checks_enabled"] is True
    assert payload["governance"]["backend"] == "python_fallback"
    assert "controlled missing" in payload["governance"]["fallback_reason"]


def test_strict_mode_rejects_a_loaded_but_unpinned_runtime(monkeypatch):
    class WrongVersionProlog:
        def query(self, goal):
            return iter([{"Major": 0, "Minor": 0, "Patch": 0}])

    monkeypatch.setitem(sys.modules, "pyswip", SimpleNamespace(Prolog=WrongVersionProlog))
    with pytest.raises(PrologBackendError, match="swipl version 0.0.0; required"):
        PrologRuleEngine(required=True)


def test_query_errors_cannot_silently_switch_to_fallback():
    class BrokenInterpreter:
        def query(self, goal):
            raise RuntimeError("controlled query failure")

    engine = PrologRuleEngine.__new__(PrologRuleEngine)
    engine.available = True
    engine._prolog = BrokenInterpreter()
    engine.info = GovernanceBackend(mode="required", backend="swipl")
    with pytest.raises(PrologBackendError, match="query failed.*controlled query failure"):
        engine.allocation_allowed(Policy.FARMING)
    assert engine.available and engine.info.backend == "swipl"


def test_pairing_rejects_mixed_backends_and_partial_identities(missing_runtime):
    raw = compare_rules(runs=1, steps=1, n_agents=3).with_columns(
        pl.lit("test").alias("experiment")
    )
    assert not pairing_errors(raw)
    partial = raw.drop("governance_mode")
    assert "governance identity is incomplete" in pairing_errors(partial)
    mixed = raw.with_columns(pl.when(pl.col("rule") == "approval")
                             .then(pl.lit("swipl"))
                             .otherwise(pl.col("governance_backend"))
                             .alias("governance_backend"))
    assert any("different governance" in error for error in pairing_errors(mixed))


def test_suite_metadata_records_disabled_backend_and_reference_pins(tmp_path):
    paths = run_experiment_suite(default_scenario_path(), output_dir=tmp_path, runs=1, steps=1)
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["governance"]["reference_versions"] == governance_versions()
    assert metadata["governance"]["observed_backends"][0]["governance_backend"] == "python"
