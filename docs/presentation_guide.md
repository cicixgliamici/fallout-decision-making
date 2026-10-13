# Presentation Guide

Use this guide to explain the project before showing detailed equations or code.
The [walkthrough](walkthrough.md) explains the process; [project status](project_status.md)
provides the evidence and remaining work behind the claims below.

## A Short Opening

> This project studies how a community makes decisions when resources are scarce.
> I compare direct voting with delegation to trusted specialists. Members receive
> imperfect information and can change their priorities as needs change. Each
> mechanism faces the same external events, so I can compare its outcomes fairly
> within the model. I measure survival and health alongside preference satisfaction
> and concentration of voting power. The result is a reproducible research
> prototype; it does not yet identify the best institution for real crises.

## A Five-Minute Explanation

1. **The political question.** Decisions can be more effective when informed
   specialists guide them, but delegation can concentrate representation.
   The project investigates that possible tradeoff under stated assumptions.
2. **The community.** Explain one member, the shared stocks, the four policies,
   and a trust link. Use the Alice/Ben/Chloe example in the walkthrough before
   describing a delegation chain.
3. **The computational method.** The simulator repeats decisions and records
   consequences. A seed reproduces a run; matching external events gives each
   mechanism the same outside conditions. Paired differences compare like with like.
4. **The measurements.** Show survival, population health, survivor health,
   satisfaction, and ballot concentration together. Explain why zero health
   dispersion can mean shared deprivation, and why high health among a few
   survivors can hide widespread death.
5. **Evidence and boundaries.** Mention the checked tests and suite with its exact
   configuration. Explain the frequent extinction and the need to examine
   material dynamics before making broader claims. Prolog and Lean have narrow,
   explicitly documented roles.

## A Small Live Demonstration

Run from an installed repository checkout:

```bash
pcds run --rule liquid_democracy --steps 5 --agents 8 --seed 42
pcds compare --steps 2 --runs 2 --agents 8 --output results/demo.csv
```

The first command shows the distinction between material outcomes and
decision-time metrics. The second creates a small reproducible comparison and
its paired exports. Two replications are a demonstration of the pipeline, not
enough evidence for a substantive ranking. Prepare a longer suite report before
the presentation rather than waiting for it during the demonstration.

## Points to Defend Clearly

**Expertise.** Specialists have smaller assumed assessment errors in one domain.
They can still choose another policy, and their decisions can still be wrong.
The model does not assume that an expert produces more food or medicine.

**Fair comparisons.** Rules share initial conditions and external draws.
Different resulting stocks, injuries, and survivor counts are still expected:
they arise from the policies and the modeled consequences. Confidence intervals
refer to variation within these assumptions, not validation against reality.

**Welfare weights.** The default weights are declared crisis priorities, not
empirically measured universal values. Contributions and alternative profiles
make their influence inspectable. Political satisfaction and concentration
remain separate so a material score does not hide representation tradeoffs.

**Undefined values.** No survivors means there is no mean survivor health; no
electorate means there is no preference or ballot-control average. Conditional
effects use pairs defined under both rules and show their coverage. This subset
can be selected by the mechanisms, so population health and survival must remain
visible beside it.

**Interdisciplinarity.** The substantive concepts are representation, trust,
expertise, and distribution of outcomes. Algorithms and controlled simulation
make their consequences inspectable. A literature-based argument and further
calibration are still required to turn this into a completed scientific study.

## Claims to Avoid

Do not say that delegation is proven superior, that the model predicts real
crises, that the project already implements strategic game theory, or that Lean
verifies the complete simulator. Do not interpret a low concentration or
dispersion value without participation, survival, and health information.

The strongest current claim is specific: the implementation compares simplified
decision mechanisms under explicit assumptions, records their material and
representational consequences, and makes the comparisons reproducible.
