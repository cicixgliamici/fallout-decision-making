# Prolog rules

The Prolog layer encodes institutional and normative constraints.

Examples:

```prolog
eligible_to_vote(A) :-
    alive(A),
    \+ sanctioned(A).

can_delegate(A, B, Topic) :-
    eligible_to_vote(A),
    eligible_to_vote(B),
    trusts(A, B),
    expert_for(B, Topic).
```

In MVP 0, Python can run without Prolog installed. When SWI-Prolog and PySwip are available, the simulator can consult `rules/governance.pl`.
