# Glossary

| Term | Meaning in this project |
| --- | --- |
| Agent | A simulated community member with a role, health, preferences, and behavioral parameters. |
| Policy | One of four collective actions chosen for a round. It changes stocks and possibly health. |
| Scenario | A JSON description of the starting community and model parameters. |
| Simulation | Executing the model's rules over successive rounds. |
| Trajectory | The complete sequence of recorded rounds for one mechanism and seed. |
| Mechanism | The procedure converting members' ballots or delegations into a collective policy choice. |
| Plurality | The option with the most first-choice votes wins; more than half the votes is not required. Called `majority` in the CLI. |
| Approval voting | Members can support several options. Here each approves their top two. |
| Expertise | A policy-specific information advantage, usually associated with a role. It reduces assumed assessment error rather than making policy effects stronger. |
| Trust graph | A directed network describing whom members may trust enough to delegate to. |
| Eligible voter | A living, unsanctioned member allowed to participate in the current decision. |
| Representative | The member whose ballot receives another member's voting weight after delegation is resolved. |
| Ordinal ranking | An ordering from preferred to less preferred options; it does not specify the size of preference differences. |
| Original priorities / prior | The member's initial ranking, retained as a stable contribution when current assessments change. This is not a Bayesian prior distribution. |
| Noise | A random error added to a member's estimate of stocks, health needs, or policy effects. |
| Gaussian error | Error drawn from a bell-shaped distribution; its spread is controlled by the configured uncertainty. |
| Seed | A recorded number that makes the pseudo-random calculations repeatable with the same code and environment. |
| Event-keyed draw | A random calculation identified by seed, event type, round, and relevant member/policy. Other events cannot shift its position. |
| Paired difference | One rule's outcome minus the baseline outcome for the same scenario, run, and seed. |
| Baseline | The reference mechanism for a comparison; paired effects use `majority`. |
| Bootstrap | Repeatedly sampling observed seed differences with replacement to estimate variation in their mean. |
| Confidence interval | An approximate uncertainty interval produced by the analysis procedure. It does not validate the model or promise where a real community's outcome will fall. |
| Conditional metric | A measure defined only when its relevant group exists, such as mean health among survivors. |
| Pair coverage | How many matched seeds have a defined value under both mechanisms, compared with all matched seeds. |
| Selection bias | A comparison can be misleading when the groups being compared depend on outcomes, such as which members or runs survive. |
| Estimand | The quantity an analysis intends to estimate, such as mean welfare difference over all seeds or health difference over pairs with survivors under both rules. |
| Welfare | An explicitly weighted material-outcome index. Its weights express priorities rather than measured universal utility. |
| Sensitivity analysis | Checking whether an interpretation changes under alternative stated assumptions, here including alternative welfare weights. |
| Concentration / HHI | An index based on squared ballot shares, normalized against equal control. It measures actual ballot control, not all political influence. |
| Resilience | Here, a proxy based on reference-normalized resource stocks. It is not a full measurement of recovery from disruption. |
| Trace digest | A compact SHA-256 fingerprint used to check whether recorded external event sequences match. |
| Schema | A named version of the output definitions, so incompatible measurements are not pooled. |
| Prolog | A language for expressing logical rules; this project's optional layer checks participation and policy admissibility. |
| Lean | A proof-checking language; current files specify a small deterministic voting/delegation core. |
| Research artifact | The runnable code, inputs, tests, and output procedures supporting investigation of a research question. |
