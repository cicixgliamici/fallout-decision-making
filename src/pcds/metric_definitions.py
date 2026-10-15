"""Define common output names, interpretation directions, and allowed absences.

A direction describes one indicator, not which institution is best overall.

This registry keeps simulation exports, statistical analysis, and validation in
agreement about column names. The schema identifies metric semantics, not a
ranking of governance rules; a delegated share is intentionally descriptive.
"""

# Conditional outcomes remain undefined when their population is absent.
# Paired analysis reports coverage explicitly rather than substituting zeros.
METRIC_DIRECTIONS = {
    "final_survival_rate": "higher",
    "final_welfare": "higher",
    "final_inequality": "lower",
    "final_resilience": "higher",
    "final_survivor_health": "higher",
    "final_population_health": "higher",
    "final_preference_satisfaction": "higher",
    "final_prior_preference_satisfaction": "higher",
    "final_delegation_concentration": "lower",
    "final_max_vote_share": "lower",
    "final_delegated_vote_share": "descriptive",
    "final_welfare_survival_priority": "higher",
    "final_welfare_health_priority": "higher",
    "final_welfare_balanced": "higher",
}
METRICS = tuple(METRIC_DIRECTIONS)
NULLABLE_METRICS = frozenset(
    {
        "final_survivor_health",
        "final_preference_satisfaction",
        "final_prior_preference_satisfaction",
        "final_delegation_concentration",
        "final_max_vote_share",
        "final_delegated_vote_share",
    }
)
METRIC_SCHEMA = "separate-outcomes-v1"
