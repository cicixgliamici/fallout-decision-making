import Lean
import Wasteland.Basic

/-!
# Executable governance and its first invariants

Read this file in four stages: contract data, the decision procedure, comparison
with an external claim, and proofs about that procedure. The Python adapter
translates a request and its witness into these types; a concrete `Conforms`
proposition is then proved with `by decide` and checked by Lean's kernel.

`Bool` is used for executable tests; `Prop` expresses statements to be proved.
`DecidableEq` supplies computable equality for data, and `Repr` supports inspection.
Neither deriving clause proves a governance property by itself.

This model does not update resources, draw random events, or attest which backend
produced a witness. General equivalence with the Python/Prolog implementations
and correctness of the JSON-to-Lean translation remain separate obligations.
-/

namespace Wasteland.Governance

/- Contract v1 is modeled independently of Python and Prolog. Naturals preserve
   exact nonnegative fractions. Parsing, reduced denominators and unique input
   identities remain obligations of the external schema adapter. -/

/-- The contract's four mechanisms. The legacy name `majority` means plurality:
    the largest first-choice count wins, without an absolute-majority requirement. -/
inductive Rule where
  | majority | approval | expert_delegation | liquid_democracy
  deriving DecidableEq, Repr

/-- Store a fraction without floating-point rounding. Positive denominators and
    reduced representations are validated externally, not enforced by this type. -/
structure ExactValue where
  numerator : Nat
  denominator : Nat
  deriving DecidableEq, Repr

/-- A role identifies an expertise domain; it does not create extra voting rights. -/
inductive Role where
  | farmer | doctor | engineer | guard | scavenger | elder
  deriving DecidableEq, Repr

/-- Derive expertise inside Lean rather than trusting an adapter-supplied domain.
    Elders share the medicine domain with doctors, as required by contract v1. -/
def expertise : Role → Policy
  | .farmer => .farming
  | .doctor | .elder => .medicine
  | .engineer | .guard => .defense
  | .scavenger => .exploration

/-- The decision-time view of one member. Eligibility flags are supplied facts;
    health and the private assessment that produced `ranking` are outside scope. -/
structure Resident where
  name : String
  role : Role
  alive : Bool
  sanctioned : Bool
  ranking : List Policy
  deriving DecidableEq, Repr

/-- One directed trust edge. Its position in the request matters on equal trust;
    `source` trusting `target` does not imply a reciprocal edge. -/
structure Link where
  source : String
  target : String
  weight : ExactValue
  deriving DecidableEq, Repr

/-- A snapshot after replenishment/assessment and before physical consequences.
    Schema validation fixes approval to two choices and liquid depth to three;
    those constants are implemented below rather than configurable in this type. -/
structure Request where
  decisionId : String
  -- Lean compares this binding string but does not recompute SHA-256 itself.
  requestHash : String
  rule : Rule
  institutionalChecks : Bool
  residents : List Resident
  links : List Link
  -- Keep every stock in the translated snapshot, although institutional
  -- permission currently reads only energy and security. No stock is spent here.
  food : ExactValue
  water : ExactValue
  medicine : ExactValue
  energy : ExactValue
  security : ExactValue
  deriving DecidableEq, Repr

/-- Ballot ownership together with its explanation. A closing cycle edge remains
    in `path`, even when `holder` returns to an earlier origin instead of its end. -/
structure Trace where
  holder : String
  path : List String
  reason : String
  deriving DecidableEq, Repr

/-- One original voter's record. Approval may list two policy contributions in
    `votes`, but the record still has exactly one voter and one final holder. -/
structure Ballot where
  voter : String
  topic : Policy
  trace : Trace
  votes : List Policy
  deriving DecidableEq, Repr

/-- Institutional permission and its reason; permission does not imply that the
    physical simulator has enough resources to execute the policy. -/
structure Permission where
  policy : Policy
  allowed : Bool
  reason : String
  deriving DecidableEq, Repr

/-- Separate the election result from the policy selected after permission checks.
    Representative pairs encode a JSON map; scores encode all four policy totals. -/
structure Decision where
  mandate : String
  eligibleVoters : List String
  representatives : List (String × String)
  scores : List (Policy × Nat)
  votedPolicy : Policy
  selectedPolicy : Policy
  permissionOverride : Bool
  deriving DecidableEq, Repr

/-- The externally supplied result to be checked, including its ballot witnesses.
    An inhabitant's opinion or a backend's reported winner is not a proof. -/
structure Claim where
  requestHash : String
  decision : Decision
  ballots : List Ballot
  permissions : List Permission
  deriving DecidableEq, Repr

/-- Shared presentation order and the fixed priority used to break policy ties. -/
def policyOrder : List Policy := [.farming, .medicine, .defense, .exploration]

/-- Filtering preserves resident order, so the witness uses a reproducible electorate. -/
def electorate (request : Request) : List Resident :=
  request.residents.filter fun resident => resident.alive && !resident.sanctioned

/-- Look up only eligible holders. The empty default makes this function total;
    valid requests and correctly resolved holders supply a complete ranking. -/
def ranking (request : Request) (name : String) : List Policy :=
  ((electorate request).find? fun resident => resident.name == name).map
    (·.ranking) |>.getD []

/-- Complete validated rankings have a head. Farming is a total-function default
    for an empty list, not an additional vote-selection mechanism. -/
def firstChoice (policies : List Policy) : Policy := policies.headD .farming

/-- Compare fractions by cross multiplication. This is an exact comparison under
    the validated positive-denominator assumption, even for nearly equal weights. -/
def heavier (challenger incumbent : Link) : Bool :=
  challenger.weight.numerator * incumbent.weight.denominator >
    incumbent.weight.numerator * challenger.weight.denominator

/-- Choose the strongest outgoing link to an eligible expert for the fixed topic.
    `none` means no candidate exists; it never invents a recipient. -/
def bestTarget (request : Request) (topic : Policy) (source : String) : Option String :=
  let candidates := request.links.filter fun link => link.source == source &&
    (electorate request).any (fun resident =>
      resident.name == link.target && expertise resident.role == topic)
  -- Scan in original edge order. Strict improvement replaces the incumbent;
  -- equal trust therefore keeps the first eligible edge, including self-edges.
  let best := candidates.foldl (fun best link => match best with
    | none => some link
    | some incumbent => some (if heavier link incumbent then link else incumbent)) none
  best.map (·.target)

/-- Structural recursion consumes one unit before another hop is possible.
    `next` supplies the candidate-selection rule, `fuel` counts remaining hops,
    and `seen` stores the path in forward order, initially including the origin.
    Decreasing fuel establishes termination even if the trust graph has cycles. -/
def follow (next : String → Option String) :
    Nat → String → String → List String → Trace
  | 0, _, current, seen => ⟨current, seen, "depth_limit"⟩
  | fuel + 1, origin, current, seen =>
    match next current with
    | none => ⟨current, seen, "no_eligible_expert"⟩
    | some target =>
      -- Example: a -> b -> c -> b closes at b, but restores a's ballot to a.
      -- The zero-fuel branch above prevents examining a would-be fourth edge.
      if target ∈ seen then ⟨origin, seen ++ [target], "cycle"⟩
      else follow next fuel origin target (seen ++ [target])

/-- Select the rule-specific ownership procedure. The topic is captured from
    the original voter once; it does not change with intermediate holders. -/
def resolve (request : Request) (voter : Resident) : Trace :=
  let next := bestTarget request (firstChoice voter.ranking)
  match request.rule with
  | .majority | .approval => ⟨voter.name, [voter.name], "direct_rule"⟩
  -- Expert delegation takes exactly one available hop, even for a self-edge.
  -- Liquid delegation instead treats a self-edge as an immediate cycle.
  | .expert_delegation => match next voter.name with
    | none => ⟨voter.name, [voter.name], "no_eligible_expert"⟩
    | some target => ⟨target, [voter.name, target], "single_hop"⟩
  | .liquid_democracy => follow next 3 voter.name voter.name [voter.name]

/-- Resolve ownership first, then read the holder's current preferences.
    Each original voter gets a separate record even when many share a holder. -/
def makeBallot (request : Request) (voter : Resident) : Ballot :=
  let trace := resolve request voter
  let preferences := ranking request trace.holder
  let votes := if request.rule == .approval then preferences.take 2
    else [firstChoice preferences]
  ⟨voter.name, firstChoice voter.ranking, trace, votes⟩

/-- Mapping creates one record per eligible voter without mutating the electorate. -/
def ballots (request : Request) : List Ballot :=
  (electorate request).map (makeBallot request)

/-- Count records supporting a policy. Delegated power is represented by multiple
    original records, not an extra multiplier attached to the final holder. -/
def score (votes : List Ballot) (policy : Policy) : Nat :=
  (votes.filter fun ballot => policy ∈ ballot.votes).length

/-- Strict improvement retains the earlier policy on a score tie. -/
def prefer (scores : Policy → Nat) (incumbent challenger : Policy) : Policy :=
  if scores incumbent < scores challenger then challenger else incumbent

/-- A three-comparison tournament in contract priority order. With all scores
    zero, farming remains the recording default for an empty electorate. -/
def winner (scores : Policy → Nat) : Policy :=
  prefer scores (prefer scores (prefer scores .farming .medicine) .defense) .exploration

/-- Compare a rational stock to an integer threshold without decimal rounding. -/
def below (value : ExactValue) (threshold : Nat) : Bool :=
  value.numerator < threshold * value.denominator

/-- Preserve the contract's short-circuit explanations: disabled checks first,
    unconditional policies next, then exploration security before energy. These
    institutional thresholds are independent of action costs in the simulator. -/
def permission (request : Request) (policy : Policy) : Permission :=
  if !request.institutionalChecks then ⟨policy, true, "checks_disabled"⟩
  else if policy == .farming || policy == .medicine then ⟨policy, true, "unconditional"⟩
  else if policy == .exploration && below request.security 15 then
    ⟨policy, false, "security_below_15"⟩
  else if below request.energy 2 then ⟨policy, false, "energy_below_2"⟩
  else ⟨policy, true, "requirements_met"⟩

/-- Apply permission after counting votes. Farming is the first allowed policy
    in this fixed profile; the election is not rerun after an override. -/
def selectedPolicy (request : Request) (voted : Policy) : Policy :=
  if (permission request voted).allowed then voted else .farming

/-- Compute the complete expected claim from the request alone. This function
    reads neither the external witness nor a Python/Prolog acceptance result. -/
def evaluate (request : Request) : Claim :=
  let votes := ballots request
  let voted := winner (score votes)
  let selected := selectedPolicy request voted
  -- An empty electorate yields a recording placeholder, not a democratic
  -- mandate. The original voted policy remains distinct from its replacement.
  ⟨request.requestHash,
    ⟨if (electorate request).isEmpty then "recording_default" else "vote",
      (electorate request).map (·.name),
      votes.map (fun ballot => (ballot.voter, ballot.trace.holder)),
      policyOrder.map (fun policy => (policy, score votes policy)),
      voted, selected, voted != selected⟩,
    votes, policyOrder.map (permission request)⟩

/-- Insert one representative pair by voter name, retaining every pair. -/
def insertOwner (owner : String × String) : List (String × String) → List (String × String)
  | [] => [owner]
  | first :: rest =>
    if owner.1 ≤ first.1 then owner :: first :: rest
    else first :: insertOwner owner rest

/-- Canonicalize map order with structural recursion that concrete kernel proofs
    can reduce directly. Contract validation has already rejected duplicate keys. -/
def sortOwners : List (String × String) → List (String × String)
  | [] => []
  | first :: rest => insertOwner first (sortOwners rest)

/-- JSON object order is immaterial; only representative maps are canonicalized.
    All ordered arrays, including paths and ballots, retain their contract order. -/
def normalize (claim : Claim) : Claim :=
  -- Structural insertion sort keeps concrete proofs reducible by the kernel.
  let owners := sortOwners claim.decision.representatives
  let decision := { claim.decision with representatives := owners }
  { claim with decision := decision }

/-- Concrete conformance means equality with this Lean procedure, up to JSON map
    order. It does not establish a separate declarative refinement theorem or
    prove that every execution of another language follows this procedure. -/
def Conforms (request : Request) (claim : Claim) : Prop :=
  normalize claim = normalize (evaluate request)

/-- Computable equality lets `by decide` construct a proof for a concrete pair.
    The kernel checks that proof; an external boolean is not accepted as evidence. -/
instance (request : Request) (claim : Claim) : Decidable (Conforms request claim) :=
  inferInstanceAs (Decidable (normalize claim = normalize (evaluate request)))

/-- Each original voter contributes one ownership record, including approval. -/
theorem ballot_count (request : Request) :
    (ballots request).length = (electorate request).length := by
  -- `simp` unfolds the definition and uses that list mapping preserves length.
  simp [ballots]

/-- Preserve the entire voter sequence, a stronger coverage statement than count
    alone. Identity uniqueness is supplied separately when needed below. -/
theorem ballot_voters (request : Request) :
    (ballots request).map (·.voter) = (electorate request).map (·.name) := by
  -- Composing the two maps projects each generated record back to its voter.
  simp [ballots, makeBallot, List.map_map]

/-- The bound includes a closing cycle edge; it does not explore a fourth edge. -/
theorem follow_path_bound (next : String → Option String) (fuel : Nat)
    (origin current : String) (seen : List String) :
    (follow next fuel origin current seen).path.length ≤ seen.length + fuel := by
  induction fuel generalizing current seen with
  | zero => simp [follow]
  | succ fuel ih =>
    -- After unfolding one hop, handle no recipient, a cycle, or recursion.
    simp only [follow]
    cases hnext : next current with
    | none => simp
    | some target =>
      simp only
      split
      · simp
      · have bound := ih target (seen ++ [target])
        -- One appended vertex consumes one unit of fuel; `omega` proves the
        -- resulting natural-number inequality from the induction hypothesis.
        simp only [List.length_append, List.length_singleton] at bound
        omega

/-- A cycle result restores the origin even when a different vertex repeats.
    The assumption concerns this Lean resolver's actual stopping reason. -/
theorem cycle_restores_origin (next : String → Option String) (fuel : Nat)
    (origin current : String) (seen : List String)
    (cycle : (follow next fuel origin current seen).reason = "cycle") :
    (follow next fuel origin current seen).holder = origin := by
  induction fuel generalizing current seen with
  -- Zero fuel cannot report a cycle, so its premise is contradictory.
  | zero => simp [follow] at cycle
  | succ fuel ih =>
    simp only [follow] at cycle ⊢
    cases hnext : next current with
    | none => simp [hnext] at cycle
    | some target =>
      simp only [hnext] at cycle ⊢
      by_cases visited : target ∈ seen
      · simp [visited]
      · simp only [if_neg visited] at cycle ⊢
        -- A cycle reported later inherits the same original voter.
        exact ih target (seen ++ [target]) cycle

/-- Holder eligibility is conditional on the next-hop selector being closed over
    the electorate. This lemma alone does not prove bestTarget's implementation. -/
theorem follow_holder_eligible (next : String → Option String) (fuel : Nat)
    (eligible : List String) (origin current : String) (seen : List String)
    (originEligible : origin ∈ eligible) (currentEligible : current ∈ eligible)
    (closed : ∀ source target, next source = some target → target ∈ eligible) :
    (follow next fuel origin current seen).holder ∈ eligible := by
  induction fuel generalizing current seen with
  | zero => exact currentEligible
  | succ fuel ih =>
    simp only [follow]
    cases hnext : next current with
    | none => exact currentEligible
    | some target =>
      by_cases visited : target ∈ seen
      · simp only [if_pos visited]
        exact originEligible
      · simp only [if_neg visited]
        -- Closure supplies eligibility of the next current holder; the origin
        -- remains eligible if a later step needs the cycle fallback.
        exact ih target (seen ++ [target]) (closed current target hnext)

/-- One comparison never lowers the score of the incumbent. -/
theorem prefer_ge_incumbent (scores : Policy → Nat) (incumbent challenger : Policy) :
    scores incumbent ≤ scores (prefer scores incumbent challenger) := by
  unfold prefer
  split <;> omega

/-- The chosen policy also scores at least as highly as the challenger. Together
    the two comparison lemmas allow the tournament proof to use transitivity. -/
theorem prefer_ge_challenger (scores : Policy → Nat) (incumbent challenger : Policy) :
    scores challenger ≤ scores (prefer scores incumbent challenger) := by
  unfold prefer
  split <;> omega

/-- The voted winner maximizes the supplied score, without claiming that scores
    measure welfare or that the winner has an absolute majority. -/
theorem winner_maximal (scores : Policy → Nat) (policy : Policy) :
    scores policy ≤ scores (winner scores) := by
  -- Each comparison contributes two inequalities: one for each contestant.
  -- Later rounds preserve the best score established by earlier rounds.
  have h₁ := prefer_ge_incumbent scores .farming .medicine
  have h₂ := prefer_ge_challenger scores .farming .medicine
  have h₃ := prefer_ge_incumbent scores (prefer scores .farming .medicine) .defense
  have h₄ := prefer_ge_challenger scores (prefer scores .farming .medicine) .defense
  have h₅ := prefer_ge_incumbent scores (prefer scores (prefer scores .farming .medicine) .defense) .exploration
  have h₆ := prefer_ge_challenger scores (prefer scores (prefer scores .farming .medicine) .defense) .exploration
  unfold winner
  -- Exhaust the four policy constructors; `omega` chains the inequalities.
  cases policy <;> omega

/-- Four-way equality retains farming, including the all-zero empty-election case. -/
theorem equal_scores_choose_farming (scores : Policy → Nat)
    (equal : ∀ policy, scores policy = scores .farming) : winner scores = .farming := by
  simp [winner, prefer, equal]

/-- The local tie rule explains why earlier policies retain priority. -/
theorem equal_scores_keep_incumbent (scores : Policy → Nat) (incumbent challenger : Policy)
    (equal : scores incumbent = scores challenger) :
    prefer scores incumbent challenger = incumbent := by
  simp [prefer, equal]

/-- Farming is permitted whether checks are enabled or disabled. This guarantees
    a permitted replacement exists in the fixed contract-v1 profile. -/
theorem farming_allowed (request : Request) : (permission request .farming).allowed = true := by
  simp [permission]
  split <;> rfl

/-- The post-election choice is permitted. It may still be unaffordable or have
    a lower electoral score than the voted winner. -/
theorem selected_allowed (request : Request) (voted : Policy) :
    (permission request (selectedPolicy request voted)).allowed = true := by
  unfold selectedPolicy
  -- Either the original winner passed permission, or farming replaces it.
  split
  · assumption
  · exact farming_allowed request

/-- Acceptance transfers a proved invariant to the externally supplied witness. -/
theorem accepted_ballot_count (request : Request) (claim : Claim)
    (accepted : Conforms request claim) :
    claim.ballots.length = (electorate request).length := by
  -- `congrArg` projects equal normalized claims to equal ballot counts.
  -- Normalization changes only map order, so the ballot invariant transfers.
  have same := congrArg (fun result : Claim => result.ballots.length) accepted
  simpa [normalize, evaluate, ballot_count] using same

/-- A conforming external witness covers the same voters in the same order. -/
theorem accepted_ballot_voters (request : Request) (claim : Claim)
    (accepted : Conforms request claim) :
    claim.ballots.map (·.voter) = (electorate request).map (·.name) := by
  have same := congrArg (fun result : Claim => result.ballots.map (·.voter)) accepted
  simpa [normalize, evaluate, ballot_voters] using same

/-- No original voter is duplicated, assuming electorate names are unique.
    `Nodup` states list uniqueness; the adapter validates this input assumption. -/
theorem accepted_unique_voters (request : Request) (claim : Claim)
    (accepted : Conforms request claim)
    (unique : ((electorate request).map (·.name)).Nodup) :
    (claim.ballots.map (·.voter)).Nodup := by
  -- Rewrite the witness's voter sequence as the already-unique electorate.
  rw [accepted_ballot_voters request claim accepted]
  exact unique

/-- The external voted winner maximizes the tally recomputed from its accepted
    ballots. Permission overrides concern `selectedPolicy`, not this winner. -/
theorem accepted_winner_maximal (request : Request) (claim : Claim)
    (accepted : Conforms request claim) (policy : Policy) :
    score claim.ballots policy ≤ score claim.ballots claim.decision.votedPolicy := by
  -- Transfer both the ballots and the voted policy, then apply the general
  -- tournament theorem. Trusting only the reported policy would be insufficient.
  have sameVotes := congrArg (fun result : Claim => result.ballots) accepted
  have sameWinner := congrArg (fun result : Claim => result.decision.votedPolicy) accepted
  simp only [normalize, evaluate] at sameVotes sameWinner
  rw [sameVotes, sameWinner]
  exact winner_maximal _ policy

/-- A conforming external decision inherits permission of its selected policy.
    This says nothing about physical execution or subsequent resource changes. -/
theorem accepted_selected_allowed (request : Request) (claim : Claim)
    (accepted : Conforms request claim) :
    (permission request claim.decision.selectedPolicy).allowed = true := by
  have same := congrArg (fun result : Claim => result.decision.selectedPolicy) accepted
  simp only [normalize, evaluate] at same
  rw [same]
  exact selected_allowed request _

end Wasteland.Governance
