# Setting & Narrative Design — Vault Governance Experiment

> **Project:** Post-Crisis Collective Decision Simulator (`fallout-decision-making`)  
> **Setting:** a Fallout-inspired underground Vault, approached as a controlled social experiment  
> **Document status:** narrative vision and development guidelines; **not** a claim that every feature below is implemented  
> **Audience:** readers, contributors, and AI coding agents

The written [Vault 47 protocol](docs/vault_protocol.md) and
[policy dictionary](docs/policy_dictionary.md) now connect this setting to the
current baseline. The [deterministic renderer and neutral event log](docs/event_reports.md)
are now implemented. Authored residents, factions, and specific incident
mechanics remain proposed.

## 1. The premise

The Vault is a deliberately demanding human-colony experiment. Its fictional
research purpose is to study self-government in isolation: how can a community
manage limited resources and unavoidable choices without outside assistance?
The same problem motivates imagined lunar bases, space settlements, and
long-duration missions. This is our narrative premise, not a historical or
canonical claim about every Fallout Vault.

Vault 47 tests which governance mechanisms best sustain the colony under
specified conditions. Survival, health, and resource reserves define material
success; representation and concentration of power expose its political costs.
The experiment can identify conditional advantages, rather than assume that
one mechanism succeeds everywhere. The Overseer reviews comparable simulated
histories; residents experience only their own history, not alternate runs.

**What happens when a community can vote on its own survival, but no one has all the information needed to keep it alive?**

Forty people live inside **Vault 47**, an isolated underground shelter built to endure a devastated outside world. Its inhabitants have different skills, beliefs, fears, and loyalties. The Vault depends on finite stores of food, water, medicine, energy, and security. Equipment degrades. Expeditions are uncertain. Some residents trust the doctors; others trust the engineers; others would rather accept a bad decision of their own than surrender their vote.

The Overseer's terminal contains a peculiar experimental protocol: rather than prescribing one permanent government, it can run the same Vault under different **collective decision-making rules**. Does a direct vote protect the community? Do specialists make better decisions? When does delegation improve outcomes, and when does it concentrate too much power?

This project turns those questions into a reproducible, inspectable simulation. **The post-apocalyptic fiction gives decisions stakes; the computational model makes their consequences testable.** Neither replaces the other.

### A one-sentence pitch

*A Vault-Tec-style governance experiment in which competing voting and delegation systems face the same crises, revealing trade-offs among survival, expertise, trust, preference satisfaction, and political power.*

### What this is — and is not

- **It is** a research-oriented, multi-agent simulation with a narrative frame, inspectable assumptions, and repeatable experiments.
- **It may become** an interactive terminal experience where readers follow a Vault's political and material history.
- **It is not** a finished game, a validated model of real societies, or a simulation of every rule and faction of the Fallout universe.
- **It is not** designed to prove that any form of government is inherently superior. Conclusions are conditional on the model and scenarios.

## 2. Tone, aesthetic, and creative boundaries

The intended feel is **retro-futurist bureaucracy meeting human catastrophe**: cheerful procedural language, cold dashboards, unsettling experiment identifiers, and difficult choices whose cost is visible in people's lives. Humor should come from institutional absurdity, not from trivializing suffering.

**Visual and writing touchstones**

- Green-on-dark terminal screens, monospaced reports, understated warning indicators, archived memos, incident logs, and population/resource dashboards.
- Terse event titles such as `WATER PURIFICATION FAILURE`, `MEDICAL PRIORITY DISPUTE`, and `OUTER AIRLOCK BREACH`.
- Institutional euphemisms contrasted with concrete outcomes: *“Reallocation successful. Four residents lost access to treatment.”*
- Short, characterful reports rather than pages of exposition or constant references to existing Fallout characters.

**Originality and intellectual-property boundary:** this is an unofficial, fan-inspired project. Vault 47, its inhabitants, factions, events, text, symbols, and assets should be original. Do not copy game dialogue, proprietary textures, music, logos, or extracted assets. Do not imply endorsement by Bethesda or ownership of Fallout. Where useful, the underlying simulator should also support a neutral, setting-independent presentation.

## 3. Vault 47: the first narrative scenario

**Vault 47** is the proposed first *authored narrative* scenario. It is **not** a claim that such a scenario, its event engine, or its factions already exist in the codebase.

**Initial fiction**

- **Population:** approximately 40 residents, with specialists and non-specialists.
- **Infrastructure:** water purification, food production, infirmary, reactor, security, and the outer airlock.
- **Institutional problem:** decisions affecting everyone must be made with uneven expertise, incomplete information, unequal trust, and competing priorities.
- **Political tension:** survival efficiency and legitimate representation may conflict.
- **Narrative viewpoint:** the reader is an analyst/Overseer reviewing experiments, **not** an all-powerful hero choosing an optimal ending.

### Factions (proposed, not implemented)

Factions add meaning only if they influence **measurable behavior**. Start small:

| Faction | Core outlook | Typical pressure | Potential blind spot |
| --- | --- | --- | --- |
| **The Stewards** | Preserve order and legitimacy within the Vault | Broad consultation, rationing, procedural fairness | Slow reaction to technical emergencies |
| **The Systems Guild** | Put complex infrastructure in expert hands | Engineering, maintenance, delegation to specialists | Technocratic concentration of power |
| **The Outriders** | Accept external risks to escape long-term decline | Exploration, trade, resource discovery | Exposure, injury, and uncertain returns |

These are **narrative starting points, not fixed moral alignments**. Members may disagree with their faction; expertise must never mechanically guarantee correctness; and factions should not secretly determine results independently of the simulated choices.

### Residents as people, not labels

Residents already have roles and modeled traits in the Python prototype. Future characterization can add **morale, faction affiliation, memory of past events, and evolving trust**, provided each added field has an explicit behavioral meaning and tests.

A character description should explain a potential choice without hard-coding one. Example: *“Dr. Mara Voss supports emergency treatment because she has seen last week's casualties; she distrusts the chief engineer after a failed repair.”* If that distrust matters, it must be represented by actual state changes or shown clearly as flavor-only narrative.

## 4. The signature incident: Water Purification Failure

> **OVERSEER TERMINAL — VAULT 47**  
> **DAY 017 / INCIDENT WP-017**  
> Water purification output has fallen below projected consumption. The engineering staff requests emergency power. The infirmary warns that diverting power may interrupt treatment. An expedition could recover parts, but the outer region is unstable. The residents must decide who should decide.

Possible **future** policy proposals include:

1. **Emergency repairs** — spend energy and parts to restore water production; potentially reduce power available to other infrastructure.
2. **Wasteland expedition** — risk injuries and supplies for uncertain repair materials.
3. **Strict rationing** — preserve reserves now but risk decreasing morale and trust.
4. **Medical-wing shutdown** — redirect power quickly at a measurable health cost.

These are **story-design examples**. The currently implemented Python simulator uses four general policies: `farming`, `medicine`, `defense`, and `exploration`. Do **not** silently present the proposals above as existing executable actions. Either map a narrative event explicitly to the current policy model, documenting the approximation, or implement a separately tested extension of the policy schema.

**The core dramatic question is not “which button is correct?” but “how does the institution change the decision, its legitimacy, and its consequences?”**

### What makes the incident scientifically useful

Run the *same* incident and initial population under several governance rules. Compare what changed, why the winning policy differed, who controlled votes, how preferences were represented, and what happened to resources and health. A plausible narrative is produced **from** the simulation trace; it must not decide the trace beforehand.

## 5. The simulation beneath the story

The proposed connection is **engine -> scenario model -> factual trace ->
narrative profile**. The engine owns general mechanics; the scenario owns the
colony's material assumptions; the profile describes the experiment and renders
its recorded outcomes. See `docs/context_architecture.md` for responsibilities,
current schema limits, and a small implementation path. Neutral events,
a deterministic renderer, and vocabulary profiles are implemented. Specific
infrastructure mechanics remain proposed.

The current Python research prototype, not this document, is the source of truth for implemented behavior. At the time of this design document, the repository includes:

- **Four decision mechanisms:** `majority` (actually first-choice plurality), `approval` (top-two approval), `expert_delegation`, and bounded `liquid_democracy`.
- **Agents** with roles, preferences, health, cooperation, risk aversion, and differing information accuracy.
- **Resources** including food, water, medicine, energy, and security; configurable policy impacts and environmental shocks.
- **Adaptive or fixed preferences**, directed trust networks, repeated rounds, and recorded decision/outcome traces.
- **Experimental comparisons** using matched seeds, paired differences, confidence intervals, and multiple outcome metrics.
- **Optional Prolog** checks for eligibility and policy admissibility; delegation itself is resolved in Python.
- **A small Lean 4 specification** with introductory theorems; it does **not** verify the Python simulator.

See `README.md`, `docs/model.md`, `docs/methods.md`, `docs/metrics.md`, `docs/limitations.md`, and `docs/project_status.md` for the detailed, current description. If the implementation changes, update those documents and **this implemented-vs-planned distinction** together.

### The experimental invariant

**Narrative should interpret outcomes, never manufacture them.** For any fixed scenario configuration and seed, the simulation must produce identical results regardless of whether a story renderer or TUI is enabled. The narrative layer must not consume or reorder the randomness used for physical dynamics or voting.

Keep distinct:

1. **World state:** residents, stocks, trust, health, infrastructure, and event flags.
2. **Decision state:** information, preferences, eligibility, ballots, delegations, and selected policy.
3. **Outcome state:** policy effects, shocks, deaths, resources, and measured political consequences.
4. **Presentation state:** terminal text, incident summaries, dialogue, and visualizations.

Prefer deterministic text templates driven by recorded facts. If procedural narrative generation is added, it must use a separate random stream and must not introduce factual claims unsupported by the run.

## 6. Design principles for all future features

### A. Consequences over decoration

A crisis should change a modeled variable: resources, health, morale, trust, infrastructure, eligibility, or the feasible action set. Purely decorative incidents must be labeled as flavor; they must not be used to explain numerical differences.

### B. Real choices, not programmed extinction

The baseline now reduces net consumption and bundles water recovery with
hydroponic food production; the original deficit-heavy scenario remains
available as `data/scenarios/shelter_alpha_legacy.json`. See
`docs/resource_balance.md` for the explicit budget and verification.
Routine energy generation is now bounded, policy inputs must be affordable,
and treatment spends medical stocks. See [physical accounting](docs/physical_accounting.md).
Fuel, infrastructure maintenance, and clinical treatment protocols remain outside
the model; closing stock budgets does not establish physical realism.

For now, strengthen the context in documentation rather than add work shifts,
new factions, or a playable incident interface. Existing simulation rounds are
computational decision cycles, not an implemented resident shift schedule.

### C. Expertise is imperfect; trust is earned or lost

A specialist should often have better *information*, not supernatural insight or an automatic productivity bonus. If trust evolves, specify a causal update based on observed outcomes, perceived accountability, or explicit incidents. Track concentration of delegated voting power and account for cycles, exclusions, and missing representatives.

### D. No predetermined winner

Do not tune event probabilities, welfare weights, or faction behavior until a favored voting rule wins. Record chosen parameters, explain their rationale, and run sensitivity analyses. Preserve inconclusive and unfavorable results.

### E. Separate survival from legitimacy

Always report survival and population health alongside representation, preference satisfaction, participation, vote concentration, and resource outcomes. A high conditional health score after most inhabitants die is not a success story. A low inequality score after extinction is not equality worth celebrating.

### F. Legibility before complexity

Introduce new state variables only with a definition, update rule, rationale, tests, and interpretable metric. A small coherent Vault with a few meaningful crises is more valuable than dozens of disconnected mechanics.

## 7. Suggested player/reader experience

The envisioned interface is an **Overseer research terminal**, not a combat game or city-builder. A typical session:

1. Select Vault 47 and a governance mechanism.
2. Read a short incident briefing and the community's current condition.
3. Inspect agents, relevant specialists, trust relationships, and available policy proposals.
4. Run a decision round; inspect ballots and delegation paths.
5. Observe resource and health changes and a terse incident aftermath.
6. Replay the same scenario with another voting mechanism **and the same seed**.
7. Compare timelines, political metrics, and material outcomes.

The eventual interface may offer an exploratory interactive mode, but **research comparisons must remain automated and intervention-free**, unless user interventions are explicitly modeled as experimental treatments.

### Example terminal vocabulary

- `VAULT STATUS` — population, health, stocks, risks.
- `CITIZEN REGISTER` — roles, preferences, eligibility, and observable trust.
- `GOVERNANCE PROTOCOL` — voting rule and delegation limits.
- `INCIDENT ARCHIVE` — event descriptions and previous decisions.
- `BALLOT TRACE` — original voter, representative, selected policy.
- `EXPERIMENT COMPARISON` — matched trajectories and clearly defined metrics.
- `POST-INCIDENT REPORT` — factual consequences, with uncertainty when relevant.

Do not imply these are existing CLI commands. The present CLI remains `pcds run`, `pcds compare`, and `pcds suite` until additional commands are implemented.

## 8. Development priorities

See the [development roadmap](docs/roadmap.md) for the proposed order of work,
current foundations, and acceptance criteria. The [status record](docs/project_status.md)
contains dated verification evidence. Keeping these separate avoids treating a
narrative proposal as an implemented feature or a historical check as a new result.

## 9. Guiding test of quality

Ask two independent questions about every milestone:

**Could a Fallout fan understand why the Vault's latest decision mattered, without reading the source code?**

**Could a mathematically or computationally trained reviewer reproduce the result and identify the assumptions on which it depends?**

If either answer is no, the milestone is not complete. The goal is not a research prototype decorated with Fallout terms, nor a game that uses numbers as atmosphere. It is **one coherent experiment with two accessible readings: a community's story and a defensible computational study of its institutions**.
