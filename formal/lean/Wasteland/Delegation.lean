import Wasteland.Basic

namespace Wasteland

/--
This file keeps delegation formalism intentionally small: it captures direct
delegation as a binary relation and states one basic sanity property.
-/

/-- A delegation relation maps one agent to another. -/
abbrev DelegatesTo := Agent -> Agent -> Prop

/-- An agent is self-delegating if they delegate to themselves. -/
def selfDelegates (R : DelegatesTo) (a : Agent) : Prop :=
  R a a

/-- A non-self-delegation relation prevents direct self-delegation. -/
def noDirectSelfDelegation (R : DelegatesTo) : Prop :=
  forall a : Agent, Not (R a a)

/-- If a relation has no direct self-delegation, no agent self-delegates. -/
theorem no_self_delegates_of_no_direct_self_delegation
    (R : DelegatesTo)
    (h : noDirectSelfDelegation R)
    (a : Agent) :
    Not (selfDelegates R a) := by
  exact h a

end Wasteland
