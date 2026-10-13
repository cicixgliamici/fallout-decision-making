import Wasteland.Basic

namespace Wasteland

/--
This file describes a direct relationship between formal agents. It does not
resolve Python's delegation chains or prove their termination or vote conservation.
-/

/-- A delegation relation maps one agent to another. -/
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
  exact h a

end Wasteland
