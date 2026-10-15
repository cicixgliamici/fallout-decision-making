# Governance Contract, Version 1

Status: **implemented** as validated data models, published JSON schemas, a Python
reference producer, an independent Python witness checker, and standalone CLI
commands. A pure Prolog producer implements the same contract and supplies live
simulation decisions when Prolog is loaded. The Python producer remains the
migration reference. [Initial Lean certification](lean_certification.md) proves
selected invariants and concrete translated conformance; general refinement and
adapter correctness remain open.

The purpose is to make the current procedure explicit before moving it between
languages. Neither a favorable election result nor a successful certificate check
establishes good governance, realistic assumptions, or a formally verified simulator.

## Boundary and Timing

A request describes one decision **after energy replenishment and preference
assessment, before policy effects and environmental pressure**. The caller supplies
the complete decision-time population, current rankings, ordered trust edges, and
stocks. Living and sanctioned flags are facts supplied by the caller; the contract
does not infer them from health. It does not perform assessment, draw random events,
update trust, spend resources, heal residents, or produce narrative text.

Version 1 specifies the simulator's four rules, top-two approval, a three-hop
liquid-delegation budget, and the current built-in institutional permissions.
Custom `approval_vote(k=...)`/`liquid_democracy_vote(max_depth=...)` helper settings
and arbitrary replacement Prolog rule files are outside this version. They remain
available through the existing interfaces; this new boundary rejects settings it
cannot faithfully describe instead of silently interpreting them differently.

`institutional_checks` is a semantic input, not a backend claim. True asks the
reference producer to evaluate the declared core permissions in Python. It does
not load SWI-Prolog. The existing `--require-prolog` execution policy, backend
versions, and source provenance remain separate runtime responsibilities. The
Prolog adapter enforces those responsibilities and implements this same contract.

## Input State

The wire schema is [request.schema.json](../data/governance/v1/request.schema.json);
its executable definition is [governance_contract.py](../src/pcds/governance_contract.py).

| Field | Meaning |
| --- | --- |
| `schema_version` | Required literal `pcds-governance-v1`. |
| `decision_id` | Nonempty caller-supplied identity binding a decision to its context; it does not affect tallying. |
| `rule` | `majority`, `approval`, `expert_delegation`, or `liquid_democracy`. |
| `institutional_checks` | Whether to apply the built-in permission filter after the vote; defaults to false. |
| `approval_k`, `delegation_max_depth` | Fixed at 2 and 3 respectively; may be omitted to use those defaults. |
| `policy_order` | Fixed sequence: farming, medicine, defense, exploration. |
| `residents` | Ordered members with unique names, role, explicit alive/sanctioned booleans, and a complete current ranking. May be empty for a standalone decision snapshot. |
| `trust_links` | Ordered, unique directed edges with source, target, and weight. Defaults to an empty list. |
| `resources` | Food, water, medicine, energy, and security stocks, all present and nonnegative. Only energy/security enter the current institutional predicates. |

Rankings must contain each policy exactly once. Roles are the current six role
identifiers. Their expertise map is part of the semantic version:

| Role | Expertise |
| --- | --- |
| doctor, elder | medicine |
| farmer | farming |
| engineer, guard | defense |
| scavenger | exploration |

This is the **shared delegation map**, including elders. Prolog's `expertise/2`
and the retained Python reference implement the same mapping. Differential tests
include elders to protect this compatibility requirement.

Historical graph endpoints that are not resident identities are permitted. They
cannot receive a vote. Dead and sanctioned recipients are likewise ignored.
Self-edges are permitted because authored graphs can contain them. Duplicate
edges are rejected; the source NetworkX graph is a simple directed graph.

### Exact Numeric Transport

Stocks and trust weights are reduced fractions:

```json
{"numerator": 2, "denominator": 1}
```

Numerators are nonnegative integers; denominators are positive integers; their
greatest common divisor must be one. Zero is always `0/1`. Trust weights must
also be at most one. Booleans and numeric strings are not accepted as integers.

The snapshot adapter preserves each finite Python float's exact rational value.
It does not round to displayed decimals or rescale resources. For example, a
binary64 value immediately below 2 stays below the energy threshold. Comparisons
can be performed using integer arithmetic; no epsilon or approximate equality is
part of the contract. Future consumers must preserve arbitrary-precision integers
when parsing JSON; converting the fields through a limited-precision number type
does not meet this contract.

### Ordering and Request Identity

Resident order determines electorate and certificate-ballot order. Among equal
trust weights, the earlier eligible outgoing edge wins. The snapshot adapter
retains NetworkX outgoing-edge order; it supplies weight zero for an edge whose
`trust` attribute is absent. Explicit wire edges always contain their weight.
Edges are not sorted by name. Reordering edges can change the selected path.

`request_sha256` is SHA-256 of the UTF-8 bytes of:

```text
pcds-governance-v1\n<normalized JSON>
```

Here `\n` denotes one newline byte. Normalized JSON is the validated request with
all defaults materialized, object keys sorted, compact separators `,` and `:`,
ASCII escaping enabled, and no trailing newline. Arrays retain their order;
fractions retain their canonical reduced form. JSON object member order and
omitted defaults do not change the digest. Every input field, including
`decision_id` and otherwise unused stocks, is bound. This conservative identity
can change even when a modification would not change the outcome.

Wire JSON is UTF-8 without a byte-order mark. Duplicate object member names,
unknown fields, invalid versions, incomplete rankings, and non-finite source
numbers are rejected. Hashing is not a signature or evidence that the supplied
facts came from a particular running simulator.

## Decision Semantics

The electorate is every supplied resident with `alive = true` and
`sanctioned = false`, in resident order. Each owns exactly one original ballot.
All four policies remain in the action space; the scenario's descriptive
`policies` field does not restrict it.

### Direct Rules

- `majority` is first-choice **plurality**, preserving its historical name. Each
  eligible voter contributes one point to their first-ranked policy.
- `approval` contributes one point to each of the voter's first two policies.
  This is still one original ballot and direct ownership when measuring power.
- Every direct ballot keeps its voter as representative, uses path `[voter]`,
  and has `stop_reason = direct_rule`.

### Candidate Selection

For a given current holder and topic, usable recipients are outgoing neighbors
who are known, living, unsanctioned specialists for that topic. Select the largest
trust weight; ties retain the original outgoing-edge order. Weight zero can win
if it is the best eligible edge. A weight is not a delegation probability.

The **topic is always the original voter's current first choice**. The terminal
holder contributes their own first choice, which may differ from that topic.
There is no majority aggregation among experts and no information-accuracy bonus
in the tally.

### Expert Delegation

Select one candidate from the original voter. If none exists, the voter retains
the ballot and the reason is `no_eligible_expert`. Otherwise the path is
`[voter, candidate]`, the candidate holds the ballot, and the reason is
`single_hop`. Stop after that transfer. A self-edge is also `single_hop`; this
rule performs no cycle detection or onward delegation.

### Liquid Delegation

Start at the original voter, with that identity already visited. For at most
three hops:

1. If the current holder has no eligible candidate for the original topic,
   stop at that holder with `no_eligible_expert`.
2. Choose the highest-priority eligible candidate and append the selected edge's
   target to the path.
3. If that identity was already visited, stop with `cycle` and restore the
   **original voter's** ballot. Keep the closing edge in the certificate.
   Do not search a lower-trust exit.
4. Otherwise move to the candidate and mark it visited.

After three noncyclic transfers, stop at the last reached holder with
`depth_limit`, without inspecting a fourth edge. This reason applies even if
that holder has no outgoing candidates. A cycle whose closing edge would be the
fourth hop is not detected within this budget.

For example, `a -> b -> c -> b` restores `a`, not `b`; `a -> b -> c -> d`
keeps `d`. A liquid self-edge closes a cycle at the first hop.

### Tally, Ties, and Empty Electorates

Count the verified contributions of every original ballot. Export integer scores
for **all four policies**, including zero scores. The largest score wins; tied
scores use the fixed policy declaration order. There is no random tie-breaker.

With no eligible voters, export empty ownership and ballot collections, all-zero
scores, `voted_policy = farming`, and `mandate = recording_default`. This is a
recording convention, not an elected mandate or a backend error. An empty
electorate does not necessarily mean extinction: all living members may be
sanctioned. Subsequent physical updates remain the simulator's responsibility.

### Post-Election Institutional Permissions

| Policy | Checks enabled | Checks disabled |
| --- | --- | --- |
| farming | Always permitted | No restriction |
| medicine | Always permitted | No restriction |
| defense | Energy at least 2 | No restriction |
| exploration | Security at least 15 and energy at least 2 | No restriction |

Record a permission entry for every policy. Disabled checks use reason
`checks_disabled`; farming/medicine use `unconditional` when enabled. Satisfied
thresholds use `requirements_met`. For blocked exploration, explain a security
violation before an energy violation if both are present, preserving the current
Python fallback's evaluation order. The reasons are `security_below_15` and
`energy_below_2`.

If the voted policy is permitted, it remains selected. Otherwise select the first
permitted policy in declaration order and set `permission_override = true`.
Do not remove options before voting, recount ballots, or change representatives.
The selected policy may therefore have fewer votes than the voted policy.

Farming and medicine are always permitted in this profile, so an all-forbidden
set cannot arise. The legacy helper's defensive farming fallback for custom
all-forbidden backends is outside this built-in profile. Such a backend must not
be labeled conformant to version 1.

Permission is separate from affordability. Defense can be permitted with 2 energy
while its physical cost is 4. The contract reports no `policy_executed` value,
resource transaction, or health effect; those are determined afterward.

## Output and Certificate

[response.schema.json](../data/governance/v1/response.schema.json) is a discriminated
union of `status = ok` and `status = error`. A successful response contains:

- `decision`: mandate, ordered electorate, original-voter-to-holder mapping,
  complete policy scores, voted policy, selected policy, and override flag;
- `certificate`: witness format `governance-witness-v1`, request digest, exactly
  one ballot witness per eligible voter, and the complete ordered permission list.

Each ballot witness contains voter, original topic, path including any cycle's
closing edge, stopping reason, terminal representative, and contributed policies.
Excluded residents must have no witness. Representative ownership has one entry
per original eligible voter, even for approval's two contributions.

The JSON schema checks structure. The independent Python checker additionally
checks complete electorate/ballot coverage, each greedy edge against **all**
eligible alternatives, stopping conditions, final ownership, contributions, all
four scores, tie-breaking, and the post-election override. Omitting an unpopular
voter or a higher-trust alternative cannot make a certificate valid.

The producer uses the existing `voting_outcome`; the checker does not invoke that
resolver or trust its reported winner. It reads contract data directly. It also
revalidates model instances because Pydantic construction bypasses can otherwise
introduce malformed data. These are executable checks; their soundness has not
yet been proved in Lean.

## Errors and Failure Policy

| Code | Meaning and current handling |
| --- | --- |
| `unsupported_version` | A request names an unsupported contract; emitted by the reference handler. |
| `invalid_request` | Supported version with invalid JSON, shape, names, numbers, rankings, rule, or parameters; emitted by the handler. Missing version is also invalid. |
| `invalid_response` | Malformed response, unsupported response shape, or an error envelope presented as a certificate; raised by the checker. |
| `request_mismatch` | Digest differs from the supplied current request; raised by the checker. |
| `invalid_certificate` | Structurally valid evidence violates the decision semantics or omits required coverage; raised by the checker. |
| `backend_unavailable` | Reserved for a future contract-aware backend adapter when the required native backend is absent. |
| `backend_version_mismatch` | Reserved for a future adapter when the required runtime version differs. |
| `rule_loading_failed` | Reserved for a future adapter when the declared rule program cannot be loaded. |
| `backend_query_failed` | Reserved for a future adapter when inference fails after loading. |

An error envelope has no decision or certificate. Its request digest is null when
no valid request could be established; failures tied to a valid request can carry
that request's digest. Existing simulator backend exceptions are unchanged; their
translation into these machine codes belongs to the next adapter step.

`govern` writes the explicit error envelope and exits with status 1 on a known
contract failure. `check-governance` reports the machine code and exits with
status 1 on failed checking. Invalid CLI paths/options use the CLI's argument-error
handling. Unexpected programming or I/O faults are not converted into farming,
accepted certificates, or backend fallbacks.

## Inspect the Example

The [request](../data/governance/v1/example_request.json) is a hand-authored
decision-time snapshot, not a measured colony trajectory. It combines equal
trust, a cycle repeating an intermediate node, a topic-dependent transfer, and
a post-election override. The [response](../data/governance/v1/example_response.json)
shows:

```text
ada:  ada -> bram -> cleo -> bram; cycle; ballot restored to ada
cleo: cleo -> dax; no further defense expert; dax votes exploration
scores: farming 1, medicine 1, defense 0, exploration 2
voted policy: exploration
selected policy: farming (security 14 is below the exploration threshold)
```

Reproduce and check it without running a simulation or native backend:

```bash
pcds govern --request data/governance/v1/example_request.json --output results/governance-response.json
pcds check-governance --request data/governance/v1/example_request.json --response results/governance-response.json
python -m pytest -q tests/test_governance_contract.py
```

An [error envelope](../data/governance/v1/example_error.json) illustrates a rejected
version. Tests also reject altered winners, omitted/duplicated ballots, lower-trust
paths, false cycle representatives, wrong permissions, and mismatched requests.
They compare all four rules with actual adaptive simulation rounds. A separate
real-Prolog suite compares complete decisions and certificates, deterministic
ties, cycles, the depth budget, exact fractions, empty electorates and matched
adaptive trajectories. The original core-permission checks remain separate cases.

Use `pcds govern --backend prolog` with the same request/output options to produce
the witness in SWI-Prolog. This requires the pinned native runtime and returns a
structured error on startup, version, rule-loading or query failure. Its adapter
transports ground dictionaries and exact integers; it does not call the Python
voting producer. The independent checker validates the response before use.
Literal resident names `true` and `false` stay names: only declared boolean fields
are decoded as booleans.

## Compatibility and Next Proof Obligations

The live simulator now uses this contract when a real Prolog backend is loaded.
The default `governance_resolver="auto"` uses Prolog in that case; runs without
Prolog keep Python voting, and optional startup failures retain a recorded Python
fallback. `governance_resolver="python_reference"` (CLI:
`--governance-resolver python_reference`) selects the previous resolver with the
same institutional checks, enabling a matched migration comparison. Native query
or witness failures stop execution and never substitute a reference decision.

Scenario files, existing commands and RNG keys are preserved. Contract validation
applies to native decision snapshots and rejects inputs outside its declared
domain. New metadata records `resolver`, `resolver_sha256` and `contract_version`
separately from backend/version/core-rule identity. Fully historical identities
remain readable; partial or mixed identities cannot support paired inference.
Per-round witnesses are checked but not stored in ordinary round exports; use
the standalone command to retain a complete request/response example.

Matched numerical behavior is checked, rather than assumed for every input.
Historical experiments retain their source identities and do not establish native
voting coverage. Regenerate an experiment when reporting results specifically as
Prolog executions; the migration audit is not a rerun of the full research study.
Before claiming Lean certification, formalize the accepted request domain
and checker and prove, at minimum:

1. Accepted certificates imply the declared complete decision semantics, including
   negative evidence that no higher-priority eligible recipient was omitted.
2. Each eligible original ballot has exactly one eligible holder; approval's
   contribution count is distinguished from ballot ownership.
3. Delegation terminates within its budget and preserves the specified cycle and
   depth behavior.
4. Tally, deterministic winner, and permission override follow from those ballots.

These obligations are **partially implemented** in the
[Lean decision model and certification command](lean_certification.md).
Selected invariants and concrete translated conformance are proved. Universal
runtime equivalence, general declarative refinement and adapter correctness
remain open. Verification of physical transitions, runtime attestation, and
empirical validation remain separate questions.

The [dated validation record](evidence/2026-10-15/governance_contract_validation.json)
records executed checks, their environments, source identities, and normalized
schema/example hashes. Earlier native-integration evidence retains its original
source identity rather than being rewritten for this new interface.
