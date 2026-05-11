from pcds.simulation import compare_rules, run_simulation


def test_run_simulation_returns_requested_number_of_steps():
    results = run_simulation(rule="majority", steps=5, n_agents=10, seed=1)
    assert len(results) == 5
    assert 0.0 <= results[-1].survival_rate <= 1.0


def test_compare_rules_returns_rows():
    df = compare_rules(rules=["majority", "approval"], runs=2, steps=3, n_agents=10, seed=1)
    assert df.height == 4
    assert set(df["rule"].to_list()) == {"majority", "approval"}
