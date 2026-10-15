:- module(pcds_governance_v1, [decide/3, expertise/2]).
:- use_module(library(apply)).
:- use_module(library(lists)).

% Contract-v1 decisions are pure relations over a complete, validated snapshot.
% No dynamic world facts, random draws, physical effects, or Python callbacks
% participate in tallying. Ordered lists retain the legacy deterministic ties.

expertise(doctor, medicine).
expertise(elder, medicine).
expertise(farmer, farming).
expertise(engineer, defense).
expertise(guard, defense).
expertise(scavenger, exploration).

decide(Request, RequestHash, Response) :-
    include(eligible, Request.residents, Electorate),
    maplist(ballot(Request, Electorate), Electorate, Ballots),
    maplist(resident_name, Electorate, Voters),
    maplist(ownership, Ballots, Owners),
    dict_create(Representatives, owners, Owners),
    maplist(policy_score(Ballots), Request.policy_order, ScorePairs),
    dict_create(Scores, scores, ScorePairs),
    winner(Request.policy_order, Scores, Voted),
    maplist(permission(Request), Request.policy_order, Permissions),
    selected_policy(Voted, Permissions, Selected, Override),
    mandate(Electorate, Mandate),
    Response = response{
        schema_version:'pcds-governance-v1', status:ok,
        decision:decision{mandate:Mandate, eligible_voters:Voters,
            representatives:Representatives, scores:Scores,
            voted_policy:Voted, selected_policy:Selected, permission_override:Override},
        certificate:certificate{schema_version:'governance-witness-v1',
            request_sha256:RequestHash, ballots:Ballots, permissions:Permissions}
    }.

eligible(Resident) :- Resident.alive == true, Resident.sanctioned == false.
resident_name(Resident, Name) :- Name = Resident.name.
ownership(Ballot, Voter-Holder) :- Voter = Ballot.voter, Holder = Ballot.representative.
mandate([], recording_default).
mandate([_|_], vote).

ballot(Request, Electorate, Voter, Ballot) :-
    Voter.ranking = [Topic|_],
    resolve(Request.rule, Request, Electorate, Voter.name, Topic, Holder, Path, Reason),
    member(Representative, Electorate), Representative.name == Holder, !,
    contributions(Request.rule, Representative.ranking, Votes),
    Ballot = ballot{voter:Voter.name, topic:Topic, path:Path,
        stop_reason:Reason, representative:Holder, votes_for:Votes}.

contributions(approval, [First, Second|_], [First, Second]) :- !.
contributions(_, [First|_], [First]).

resolve(majority, _, _, Voter, _, Voter, [Voter], direct_rule).
resolve(approval, _, _, Voter, _, Voter, [Voter], direct_rule).
resolve(expert_delegation, Request, Electorate, Voter, Topic, Holder, Path, Reason) :-
    ( best_target(Request.trust_links, Electorate, Voter, Topic, Target) ->
        Holder = Target, Path = [Voter, Target], Reason = single_hop
    ; Holder = Voter, Path = [Voter], Reason = no_eligible_expert
    ).
resolve(liquid_democracy, Request, Electorate, Voter, Topic, Holder, Path, Reason) :-
    follow(Request.delegation_max_depth, Request.trust_links, Electorate,
        Voter, Voter, Topic, [Voter], Holder, Path, Reason).

% The budget is checked before looking for another edge. A cycle closed on the
% third hop restores the origin; a would-be fourth closing edge is never visited.
follow(0, _, _, _, Current, _, Seen, Current, Path, depth_limit) :- !,
    reverse(Seen, Path).
follow(Budget, Edges, Electorate, Origin, Current, Topic, Seen, Holder, Path, Reason) :-
    ( best_target(Edges, Electorate, Current, Topic, Target) ->
        ( memberchk(Target, Seen) ->
            Holder = Origin, reverse([Target|Seen], Path), Reason = cycle
        ; Remaining is Budget - 1,
          follow(Remaining, Edges, Electorate, Origin, Target, Topic,
              [Target|Seen], Holder, Path, Reason)
        )
    ; Holder = Current, reverse(Seen, Path), Reason = no_eligible_expert
    ).

best_target(Edges, Electorate, Source, Topic, Target) :-
    include(candidate(Electorate, Source, Topic), Edges, Candidates),
    Candidates = [First|Rest],
    foldl(prefer_strictly_heavier, Rest, First, Best),
    Target = Best.target.

candidate(Electorate, Source, Topic, Edge) :-
    Edge.source == Source,
    member(Resident, Electorate), Resident.name == Edge.target,
    expertise(Resident.role, Topic).

prefer_strictly_heavier(Challenger, Incumbent, Best) :-
    % Cross products compare exact fractions, including weights too close to
    % distinguish through rounded decimal transport. Equality keeps the first edge.
    ( Challenger.weight.numerator * Incumbent.weight.denominator >
      Incumbent.weight.numerator * Challenger.weight.denominator -> Best = Challenger
    ; Best = Incumbent
    ).

policy_score(Ballots, Policy, Policy-Score) :-
    include(approves_policy(Policy), Ballots, Supporting), length(Supporting, Score).
approves_policy(Policy, Ballot) :- memberchk(Policy, Ballot.votes_for).

winner([First|Rest], Scores, Winner) :- foldl(prefer_higher_score(Scores), Rest, First, Winner).
prefer_higher_score(Scores, Challenger, Incumbent, Best) :-
    ( get_dict(Challenger, Scores, New), get_dict(Incumbent, Scores, Old), New > Old ->
        Best = Challenger
    ; Best = Incumbent
    ).

permission(Request, Policy, Permission) :-
    permission_reason(Request.institutional_checks, Policy, Request.resources, Allowed, Reason),
    Permission = permission{policy:Policy, allowed:Allowed, reason:Reason}.
permission_reason(false, _, _, true, checks_disabled) :- !.
permission_reason(true, Policy, _, true, unconditional) :- memberchk(Policy, [farming, medicine]), !.
permission_reason(true, exploration, Stocks, false, security_below_15) :-
    below(Stocks.security, 15), !.
permission_reason(true, _, Stocks, false, energy_below_2) :- below(Stocks.energy, 2), !.
permission_reason(true, _, _, true, requirements_met).
below(Value, Threshold) :- Value.numerator < Threshold * Value.denominator.

selected_policy(Voted, Permissions, Selected, Override) :-
    ( member(Permission, Permissions), Permission.policy == Voted, Permission.allowed == true ->
        Selected = Voted, Override = false
    ; member(FirstAllowed, Permissions), FirstAllowed.allowed == true, !,
      Selected = FirstAllowed.policy, Override = true
    ).
