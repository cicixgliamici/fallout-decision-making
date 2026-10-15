"""Write a reproducible matched-trajectory migration audit using real SWI-Prolog.

Run from the checkout: python experiments/check_governance_migration.py --output results/migration
This is a conformance audit, not a study of which voting mechanism is preferable.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform

from pcds.governance_contract import parse_request
from pcds.governance_prolog import decide_prolog
from pcds.governance_reference import decide_governance
from pcds.prolog_rules import PrologRuleEngine
from pcds.provenance import source_fingerprints
from pcds.scenarios import default_scenario_path, load_scenario
from pcds.simulation import run_simulation
from pcds.voting import VOTING_RULES


def compare_trajectory(rule: str, seed: int, scenario, steps: int) -> dict:
    """Compare all recorded state, events and randomness, excluding backend identity."""
    options = dict(rule=rule, steps=steps, seed=seed, scenario=scenario,
                   require_prolog=True, record_events=True)
    reference = run_simulation(**options, governance_resolver="python_reference")
    native = run_simulation(**options)
    different = [left.step for left, right in zip(reference, native)
                 if left.model_dump(exclude={"governance"}) != right.model_dump(exclude={"governance"})]
    return {"rule": rule, "seed": seed, "rounds": len(native), "different_rounds": different,
            "inactive_rounds": sum(item.policy_block_reason == "no_living_residents" for item in native),
            "blocked_rounds": sum((item.policy_block_reason or "").startswith("insufficient_") for item in native),
            "native_governance": native[-1].governance.model_dump(),
            "reference_governance": reference[-1].governance.model_dump()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/migration"))
    args = parser.parse_args()
    engine = PrologRuleEngine(required=True)
    scenario = load_scenario(default_scenario_path())
    scenario.agents = 8
    steps, seeds = 40, [1, 42, 123]
    pairs = [compare_trajectory(rule, seed, scenario, steps)
             for rule in VOTING_RULES for seed in seeds]
    root = Path(__file__).resolve().parents[1]
    request = parse_request((root / "data/governance/v1/example_request.json").read_text(encoding="utf-8"))
    response = decide_prolog(request, engine)
    example_matches = response == decide_governance(request)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    example_bytes = (response.model_dump_json(indent=2) + "\n").encode("utf-8")
    (output / "prolog_response.json").write_bytes(example_bytes)
    report = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Migration conformance; no empirical or Lean verification claim",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "source_fingerprints": source_fingerprints(),
        "audit_script_sha256": sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "scenario": scenario.model_dump(mode="json"), "seeds": seeds, "steps": steps,
        "trajectory_pairs": pairs, "compared_rounds": sum(item["rounds"] for item in pairs),
        "example_matches_reference": example_matches,
        "example_response_sha256": sha256(example_bytes).hexdigest(),
        "passed": example_matches and not any(item["different_rounds"] for item in pairs),
    }
    (output / "migration_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Matched {len(pairs)} trajectories / {report['compared_rounds']} rounds; passed={report['passed']}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
