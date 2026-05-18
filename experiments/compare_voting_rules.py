from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from pcds.scenarios import default_scenario_path
from pcds.simulation import compare_rules


def main() -> None:
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = compare_rules(runs=30, steps=35, n_agents=50, seed=7, scenario=default_scenario_path())
    df.write_csv(output_dir / "comparison.csv")

    summary = df.group_by("rule").mean().sort("final_welfare", descending=True)
    print(summary)

    rules = summary["rule"].to_list()
    welfare = summary["final_welfare"].to_list()

    plt.figure(figsize=(8, 5))
    plt.bar(rules, welfare)
    plt.title("Mean final welfare by voting rule")
    plt.xlabel("Voting rule")
    plt.ylabel("Mean final welfare")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(output_dir / "welfare_by_rule.png")


if __name__ == "__main__":
    main()
