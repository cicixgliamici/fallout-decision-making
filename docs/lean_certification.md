# First Lean Governance Certificates

Status: **partially implemented certification**. Lean 4.19.0 now models contract-v1
decisions, proves selected general invariants, and checks concrete translated
request/witness pairs with its kernel. This is not verification of every Python
or Prolog execution, the JSON adapter, or the physical simulation.

## What Lean Checks

[Governance.lean](../formal/lean/Wasteland/Governance.lean) independently computes
eligibility, role expertise including elders, exact trust comparisons, ordered
expert selection, delegation paths, stopping reasons, contributions, tally,
winner, policy permissions and overrides. The original topic remains fixed;
cycles restore the original voter; a three-hop budget is checked before another
edge is explored. Approval contributes two policy choices but keeps one ownership
record per voter. Representative-map order is ignored, while ordered arrays
retain their contract meaning.

`Conforms request claim` means that the supplied claim equals the result of this
Lean procedure, after canonicalizing representative-map order. The concrete proof
uses `by decide`: Lean constructs and kernel-checks a proof of this proposition.
It does not accept a Python boolean, invoke the Python witness checker, or use
`native_decide`. A false proposition cannot produce a successful receipt.

The library adds 17 theorems, including supporting lemmas. Main results are:

| Theorem | Statement and assumptions |
| --- | --- |
| `follow_path_bound` | At most `fuel` additional edges are retained, including a closing cycle edge. Structural recursion also establishes termination of the Lean procedure. |
| `cycle_restores_origin` | A result marked as a cycle returns ownership to the original voter, including an intermediate-node repetition. |
| `follow_holder_eligible` | Ownership remains eligible **assuming** origin/current eligibility and closure of the next-hop function over the electorate. This does not by itself prove closure of `bestTarget`. |
| `ballot_count`, `ballot_voters` | There is one ownership record for each eligible original voter, in electorate order. |
| `winner_maximal` | No policy has a higher score than the voted winner. |
| `equal_scores_keep_incumbent`, `equal_scores_choose_farming` | Equal scores preserve the incumbent; a four-way tie chooses farming. |
| `selected_allowed` | The policy after the institutional override is permitted. Physical affordability is a separate question. |
| `accepted_*` | Accepted claims inherit ballot count, voter coverage, winner maximality and selected-policy permission. Voter uniqueness additionally assumes unique electorate identities. |

These proofs concern the Lean functions. The concrete certificate connects one
external witness to those functions. A general refinement proof between this
procedure and an independently stated declarative specification is not complete;
neither is a proof of universal equivalence to Prolog or Python.

## Use the Command

With both pinned native toolchains available:

```bash
pcds govern --backend prolog --request data/governance/v1/example_request.json --output results/prolog-response.json
pcds certify-governance --request data/governance/v1/example_request.json --response results/prolog-response.json --output-dir results/lean-certificate
```

The output directory must be new. A successful invocation retains:

- `GovernanceCertificate.lean`: readable input, claimed witness, conformance proof
  and corollaries about original ballots/voters;
- `GovernanceCertificate.olean`: compiled proof artifact;
- `certification.json`: request/response/source/proof hashes, toolchain version,
  source fingerprints, actual axiom report, trusted boundary and excluded claims.

Failed attempts may retain source for inspection but receive no successful
receipt. Missing tools, an incorrect Lean version, build errors and false claims
are explicit failures. Existing `check-governance` remains a Python check;
ordinary simulation runs do not invoke Lean automatically.

The adapter validates the versioned JSON schema and translates literal data.
Exact nonnegative fractions remain integer pairs. It translates role constructors;
Lean derives expertise itself. JSON parsing, schema constraints, SHA-256 binding
and faithful literal translation remain trusted Python responsibilities. The
formal model assumes the validated profile: four complete rankings, top-two
approval, depth three, positive denominators and unique resident/edge identities.
The example's proof reports the standard Lean axiom `propext`; no custom axiom,
`sorry` admission or native-evaluation axiom is introduced.

## Reproduce the Checks

```bash
cd formal/lean
lake build Wasteland
cd ../..
python -m pytest -q -m lean tests/integration
```

The library is now an explicit default build target. Previously `lake build`
could succeed without compiling any library target, so the earlier recorded
success was insufficient evidence that its modules compiled. The new integration
test explicitly requests `Wasteland` and requires `Governance.olean` to exist.
The Lean CI job selects all Lean integration tests.

The [retained example and validation record](evidence/2026-10-15/lean_certification)
show the scope actually checked. No dynamics, RNG keys, voting rules or export
schema are changed by this optional step; existing numerical experiments need
no regeneration for a mechanism change. Historical source identities stay intact.
