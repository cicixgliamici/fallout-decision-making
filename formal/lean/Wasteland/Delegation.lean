import Wasteland.Basic

/-!
# A minimal relational example

This older module introduces how assumptions about a relation are used in Lean.
For executable bounded paths and cycle fallback, read Governance.follow and its
proofs instead. A prohibition on self-edges alone cannot rule out longer cycles.
-/

namespace Wasteland

/-
This file describes a direct relationship between formal agents. It does not
resolve Python's delegation chains or prove their termination or vote conservation.
-/

/-- A proposition about an ordered pair of agents. A relation need not assign
    exactly one recipient, so this type alone is not a deterministic resolver. -/
abbrev DelegatesTo := Agent -> Agent -> Prop

/-- An agent is self-delegating if they delegate to themselves. -/
def selfDelegates (R : DelegatesTo) (a : Agent) : Prop :=
  R a a

/-- A non-self-delegation relation prevents direct self-delegation. -/
def noDirectSelfDelegation (R : DelegatesTo) : Prop :=
  forall a : Agent, Not (R a a)

/--
Unpack the no-self-delegation assumption for one agent. This conclusion follows
from the definition; longer cycles are outside this small statement's scope.
-/
theorem no_self_delegates_of_no_direct_self_delegation
    (R : DelegatesTo)
    (h : noDirectSelfDelegation R)
    (a : Agent) :
    Not (selfDelegates R a) := by
  -- The universal assumption h already excludes R a a for any chosen a.
  -- Applying h to this particular agent completes the proof; it does not
  -- inspect a path or analyze a trust graph.
  exact h a

end Wasteland
