namespace Wasteland

/--
Policies are the formal counterpart of the simulator's small action space.
The Lean core deliberately models only the choice structure, not stochastic
resource dynamics.
-/
inductive Policy where
  | farming
  | medicine
  | defense
  | exploration
  deriving DecidableEq, Repr

/-- A formal agent has only an identifier; health, roles, and trust are not modeled here. -/
structure Agent where
  id : Nat
  deriving DecidableEq, Repr

/--
A ballot assigns a natural-number score to each policy. This is broad enough to
represent approval-style ballots while keeping the formal core compact.
-/
abbrev Ballot := Policy -> Nat
abbrev Score := Policy -> Nat

/-- An agent approves a policy when its ballot gives the policy a positive score. -/
def approves (b : Ballot) (p : Policy) : Prop :=
  b p > 0

/-- A policy has at least another policy's score; this is not a welfare comparison. -/
def weaklyDominates (score : Score) (p q : Policy) : Prop :=
  score p >= score q

/-- A policy is a winner if it weakly dominates every other policy. -/
def isWinner (score : Score) (p : Policy) : Prop :=
  forall q : Policy, weaklyDominates score p q

/--
This proof unpacks the winner definition: the hypothesis already supplies every
required comparison. It does not verify Python's tally, tie-breaking, or simulator.
-/
theorem winner_of_max_score
    (score : Score)
    (p : Policy)
    (h : forall q : Policy, score p >= score q) :
    isWinner score p := by
  intro q
  exact h q

end Wasteland
