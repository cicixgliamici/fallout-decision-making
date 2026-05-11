% Minimal normative governance rules for MVP 0.
% These rules are intentionally small and readable.

% Dynamic facts are asserted from Python when PySwip is available.
:- dynamic alive/1.
:- dynamic sanctioned/1.
:- dynamic role/2.
:- dynamic trusts/2.

allowed_policy(farming).
allowed_policy(medicine).
allowed_policy(defense).
allowed_policy(exploration).

eligible_to_vote(A) :-
    alive(A),
    \+ sanctioned(A).

expert_for(A, medicine) :- role(A, doctor).
expert_for(A, farming) :- role(A, farmer).
expert_for(A, defense) :- role(A, guard).
expert_for(A, defense) :- role(A, engineer).
expert_for(A, exploration) :- role(A, scavenger).

can_delegate(A, B, Topic) :-
    eligible_to_vote(A),
    eligible_to_vote(B),
    trusts(A, B),
    expert_for(B, Topic).
