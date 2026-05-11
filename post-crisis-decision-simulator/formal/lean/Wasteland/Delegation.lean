namespace Wasteland

structure Agent where
  id : Nat
  deriving DecidableEq, Repr

/-- A delegation relation maps one agent to another. -/
abbrev DelegatesTo := Agent → Agent → Prop

/-- An agent is self-delegating if they delegate to themselves. -/
def selfDelegates (R : DelegatesTo) (a : Agent) : Prop :=
  R a a

/-- MVP 0 placeholder: a non-self-delegation relation prevents direct self-delegation. -/
def noDirectSelfDelegation (R : DelegatesTo) : Prop :=
  ∀ a : Agent, ¬ R a a

/-- Simple theorem: if a relation has no direct self-delegation, no agent self-delegates. -/
theorem no_self_delegates_of_no_direct_self_delegation
    (R : DelegatesTo)
    (h : noDirectSelfDelegation R)
    (a : Agent) :
    ¬ selfDelegates R a := by
  exact h a

end Wasteland
