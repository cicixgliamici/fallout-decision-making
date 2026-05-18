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

/-- A policy weakly dominates another under a score function. -/
def weaklyDominates (score : Score) (p q : Policy) : Prop :=
  score p >= score q

/-- A policy is a winner if it weakly dominates every other policy. -/
def isWinner (score : Score) (p : Policy) : Prop :=
  forall q : Policy, weaklyDominates score p q

/-- If a policy's score is at least every other score, then it is a winner by definition. -/
theorem winner_of_max_score
    (score : Score)
    (p : Policy)
    (h : forall q : Policy, score p >= score q) :
    isWinner score p := by
  intro q
  exact h q

end Wasteland
