"""Measure survival, health, preference agreement, and actual ballot control.

Report separate dimensions because a low dispersion or high conditional mean can mislead.

These are read-only measurements, never decision inputs. Survival and population
health use all original members; survivor health uses living members; satisfaction
and ballot control use the decision-time electorate supplied by the caller.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from pcds.models import Agent, CommunityState, Policy, ResourceReference, WelfareWeights

# Prespecified alternative priorities expose sensitivity without rerunning or
# changing the physical model. They are normative choices, not fitted weights.
WELFARE_PROFILES = {
    "survival_priority": WelfareWeights(survival=0.80, health=0.15, resources=0.05),
    "health_priority": WelfareWeights(survival=0.45, health=0.45, resources=0.10),
    "balanced": WelfareWeights(survival=0.50, health=0.30, resources=0.20),
}


def survival_rate(agents: list[Agent]) -> float:
    """Report the living fraction of all original members, not of current voters."""
    return sum(agent.alive for agent in agents) / len(agents) if agents else 0.0


def survivor_health(agents: list[Agent]) -> float | None:
    """Report mean health among living members; return None when none remain."""
    healths = [agent.health for agent in agents if agent.alive]
    # A vanished population has no conditional mean; reporting zero would
    # conflate absence of survivors with an observed health level.
    return sum(healths) / len(healths) if healths else None


def population_health(agents: list[Agent]) -> float:
    """Retain deaths in the denominator by assigning them zero health."""
    # With two original members, one survivor at health 0.8 gives survivor health
    # 0.8 and population health 0.4. This prevents deaths from improving this mean.
    return sum(agent.health for agent in agents if agent.alive) / len(agents) if agents else 0.0


def welfare_components(
    agents: list[Agent],
    state: CommunityState,
    weights: WelfareWeights | None = None,
    reference: ResourceReference | None = None,
) -> dict[str, float]:
    """Expose the three weighted material contributions rather than hiding priorities.

    Reserve rewards are capped and survival-gated; health retains the original population.
    """
    weights = weights or WelfareWeights()
    survival = survival_rate(agents)
    # Health uses the original population denominator, and reserves are both
    # capped and gated by survival. Abundant stocks cannot reward extinction.
    return {
        "survival": weights.survival * survival,
        "health": weights.health * population_health(agents),
        "resources": weights.resources * survival * min(1.0, resource_resilience(state, reference)),
    }


def social_welfare(
    agents: list[Agent],
    state: CommunityState,
    weights: WelfareWeights | None = None,
    reference: ResourceReference | None = None,
) -> float:
    """Sum the explicit material contributions, with configurable normative weights.

    Satisfaction and concentration remain separate so this index cannot conceal them.
    """
    return sum(welfare_components(agents, state, weights, reference).values())


def health_inequality(agents: list[Agent]) -> float:
    # Population dispersion is descriptive only. Deaths receive zero health,
    # independent of the simulator's positive numerical death threshold.
    """Report population health dispersion with zero assigned to deaths.

    Zero dispersion can mean shared good health, deprivation, or extinction.
    """
    healths = [agent.health if agent.alive else 0.0 for agent in agents]
    return float(np.std(healths)) if healths else 0.0


def resource_resilience(state: CommunityState, reference: ResourceReference | None = None) -> float:
    """Average stock-to-reference ratios, retaining values above one for surpluses.

    This stock proxy does not guarantee that each essential supply is adequate.
    """
    reference_stocks = (reference or ResourceReference()).model_dump()
    return sum(value / reference_stocks[name] for name, value in state.as_dict().items()) / len(
        reference_stocks
    )


def preference_satisfaction(
    voters: list[Agent],
    policy: Policy,
    priors: dict[str, tuple[Policy, ...]] | None = None,
) -> float | None:
    """Average the selected policy's normalized rank among eligible voters.

    Use current rankings or supplied original priorities; equal rank spacing is a convention.
    This measures decision agreement even if physical affordability blocks execution.
    """
    voters = [voter for voter in voters if voter.alive and not voter.sanctioned]
    if not voters:
        return None
    scores = []
    for voter in voters:
        ranking = priors[voter.name] if priors is not None else voter.preferences
        # Equal rank spacing is an explicit reporting convention, not a claim
        # that agents possess comparable cardinal utilities.
        scores.append((len(ranking) - 1 - ranking.index(policy)) / (len(ranking) - 1))
    return sum(scores) / len(scores)


def delegation_power(representatives: dict[str, str]) -> dict[str, float | None]:
    """Measure who controls the electorate's original ballots after actual resolution.

    A missing electorate has undefined power measures; a sole voter has no excess
    delegation concentration but necessarily controls a ballot share of one.
    """
    population = len(representatives)
    if population == 0:
        return {
            "delegation_concentration": None,
            "max_vote_share": None,
            "delegated_vote_share": None,
        }
    shares = [weight / population for weight in Counter(representatives.values()).values()]
    # Equal control of four ballots gives HHI = 4 * (1/4)^2 = 1/4;
    # one holder controlling all four gives HHI = 1 before normalization.
    hhi = sum(share * share for share in shares)
    # Squared shares emphasize large blocks of controlled votes. The index uses
    # actual resolved ballot weights, not a member's number of network links.
    # Normalize against equal control of N original ballots. A sole voter
    # has no delegation-induced concentration; their absolute share is still 1.
    concentration = (hhi - 1.0 / population) / (1.0 - 1.0 / population) if population > 1 else 0.0
    return {
        "delegation_concentration": min(1.0, max(0.0, concentration)),
        "max_vote_share": max(shares),
        "delegated_vote_share": sum(
            voter != representative for voter, representative in representatives.items()
        )
        / population,
    }
