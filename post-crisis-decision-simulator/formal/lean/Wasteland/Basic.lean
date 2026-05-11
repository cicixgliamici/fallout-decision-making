namespace Wasteland

inductive Policy where
  | farming
  | medicine
  | defense
  | exploration
  deriving DecidableEq, Repr

structure Agent where
  id : Nat
  deriving DecidableEq, Repr

abbrev Ballot := Policy → Nat
abbrev Profile := Agent → Ballot

/-- A tiny approval-style relation: an agent approves a policy when its ballot gives
    the policy a positive score. -/
def approves (b : Ballot) (p : Policy) : Prop :=
  b p > 0

/-- A policy weakly dominates another under a score function. -/
def weaklyDominates (score : Policy → Nat) (p q : Policy) : Prop :=
  score p ≥ score q

/-- A policy is a winner if it weakly dominates every other policy. -/
def isWinner (score : Policy → Nat) (p : Policy) : Prop :=
  ∀ q : Policy, weaklyDominates score p q

/-- Basic sanity theorem: if a policy's score is at least every other score,
    then it is a winner by definition. -/
theorem winner_of_max_score
    (score : Policy → Nat)
    (p : Policy)
    (h : ∀ q : Policy, score p ≥ score q) :
    isWinner score p := by
  intro q
  exact h q

end Wasteland
