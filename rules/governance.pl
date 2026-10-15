% Compatibility predicates for institutional queries. The pure contract resolver
% in governance_decision.pl now owns complete elections, including delegation.
:- use_module(governance_decision, [expertise/2]).

% Dynamic facts are asserted from Python when PySwip is available.
:- dynamic alive/1.
:- dynamic sanctioned/1.
:- dynamic role/2.
:- dynamic trusts/2.
:- dynamic resource/2.

allowed_policy(farming).
% These thresholds express permission, not a complete resource-feasibility test.
allowed_policy(medicine).
allowed_policy(defense) :- resource(energy, E), E >= 2.0.
allowed_policy(exploration) :-
    resource(security, S),
    resource(energy, E),
    S >= 15.0,
    E >= 2.0.

eligible_to_vote(A) :-
    alive(A),
    \+ sanctioned(A).

% Share the role map with the actual resolver, including elders as medicine
% specialists. This avoids a second, subtly different definition of expertise.
expert_for(A, Topic) :- role(A, Role), expertise(Role, Topic).

can_delegate(A, B, Topic) :-
    eligible_to_vote(A),
    eligible_to_vote(B),
    trusts(A, B),
    expert_for(B, Topic).
