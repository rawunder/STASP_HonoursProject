%%% Final Optimized Model (Monolithic)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Part 1: Problem Generator and Domain Definitions
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- Domain Definitions from Facts ---
% These facts are expected to be in the instance file.
% e.g., team(0..19). slot(0..37). num_teams(20). num_slots(38).
team(T) :- team(T, _).
slot(S) :- slot(S, _).

% --- Timetable Generator ---
% The core of the model. It generates possible timetables.

% 1. Complete Schedule: Team-based generation,
%For every team T and for every time slot S, that team T must play exactly one game in that slot S, 
%either as the home team or as the away team.
1 { schedule(T,T2,S) : team(T2), T2 != T; schedule(T1,T,S) : team(T1), T1 != T } 1 :- team(T), slot(S).

%%% Preprocessing Constraints Only

%% =============================================================================
%% PREPROCESSING AS INTEGRITY CONSTRAINTS
%% =============================================================================

%%% Preprocessing rules adapted to act as constraints on the main model.

%%% Forbidden assignments from domain_reduction.lp
forbidden_home(T,S) :- ca1_param(ID,type,hard), ca1_param(ID,max,0), ca1_param(ID,mode,"H"), ca1_teams(ID,T), ca1_slots(ID,S).
forbidden_away(T,S) :- ca1_param(ID,type,hard), ca1_param(ID,max,0), ca1_param(ID,mode,"A"), ca1_teams(ID,T), ca1_slots(ID,S).
forbidden_meeting(T1,T2,S) :- ga1_param(ID,type,hard), ga1_param(ID,max,0), ga1_meetings(ID,T1,T2), ga1_slots(ID,S).

%%% Add integrity constraints based on preprocessing
:- schedule(T, _, S), forbidden_home(T, S).
:- schedule(_, T, S), forbidden_away(T, S).
:- schedule(T1, T2, S), forbidden_meeting(T1, T2, S).

% Game-based generation
%{ schedule(T1, T2, S) : slot(S) } = 1 :- team(T1), team(T2), T1 != T2.

% 2. No Concurrent Games: Each team plays at most one game per slot.
%    This is a fundamental hard constraint, enforced below.
%    The generator ensures each team plays T-1 home and T-1 away games total.
% 2a. Each team plays exactly NumTeams-1 home games in total.
% We specify that the opponent (T2) must be a team and not the same team (T).
NumTeams-1 { schedule(T, T2, S) : slot(S), team(T2), T != T2 } NumTeams-1 :-
    team(T), num_teams(NumTeams).
% 2b. Each team plays exactly NumTeams-1 away games in total.
% Similarly, the opponent (T1) must be a team and not the same team (T).
NumTeams-1 { schedule(T1, T, S) : slot(S), team(T1), T1 != T } NumTeams-1 :-
    team(T), num_teams(NumTeams).

% Each team plays exactly one home game against each other team
1 { schedule(T1, T2, S) : slot(S) } 1 :- team(T1), team(T2), T1 != T2.

% Each team plays exactly one away game against each other team  
1 { schedule(T2, T1, S) : slot(S) } 1 :- team(T1), team(T2), T1 != T2.
    
%A team plays at most one game per slot.
:- team(T), slot(S), #count{ Opponent : schedule(T, Opponent, S);
                            Opponent : schedule(Opponent, T, S) } > 1.



% --- Helper Predicates ---
% Defines when a team is playing in a slot (either home or away).
plays(T, S) :- schedule(T, _, S), team(T), slot(S).
plays(T, S) :- schedule(_, T, S), team(T), slot(S).

% Defines home/away breaks. A break occurs if a team has two consecutive home or away games.
is_break(T, S, home) :- schedule(T, _, S-1), schedule(T, _, S), slot(S), S > 0.
is_break(T, S, away) :- schedule(_, T, S-1), schedule(_, T, S), slot(S), S > 0.
is_break(T, S) :- is_break(T, S, home).
is_break(T, S) :- is_break(T, S, away).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Part 2: Hard Constraint Enforcement
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- Fundamental Hard Constraints ---
% A team can play at most one game in any single slot.
:- team(T), slot(S), #count{ T2 : schedule(T, T2, S); T2 : schedule(T2, T, S) } > 1.
:- schedule(T1, T2, S), schedule(T2, T1, S), team(T1), team(T2), slot(S), T1 != T2.

% Phased Constraint: If a tournament is phased, games cannot be repeated
% (e.g., A vs B and B vs A) in the same half of the season.
% This is enforced by ensuring they don't play each other (regardless of home/away) twice in a half.
:- phased, num_slots(NS), schedule(T1, T2, S1), schedule(T2, T1, S2), S1 < NS/2, S2 < NS/2.
:- phased, num_slots(NS), schedule(T1, T2, S1), schedule(T2, T1, S2), S1 >= NS/2, S2 >= NS/2.


% --- Constraint CA1: Capacity on Home/Away Games ---
% Forbids a solution if a team plays more than MAX home/away games in a set of slots.
:- ca1_param(ID, type, hard), ca1_param(ID, max, Max), ca1_param(ID, mode, "H"), ca1_teams(ID, Team),
   #count { Slot : schedule(Team, _, Slot), ca1_slots(ID, Slot) } > Max.

:- ca1_param(ID, type, hard), ca1_param(ID, max, Max), ca1_param(ID, mode, "A"), ca1_teams(ID, Team),
   #count { Slot : schedule(_, Team, Slot), ca1_slots(ID, Slot) } > Max.


% --- Constraint CA2: Capacity on Games vs. Opponent Set ---
% Forbids a solution if a team plays more than MAX games (H, A, or HA) against a specific set of opponents within a given set of slots.
:- ca2_param(ID, type, hard), ca2_param(ID, max, Max), ca2_param(ID, mode1, "H"), ca2_teams1(ID, T1),
   #count { T2, S : schedule(T1, T2, S), ca2_teams2(ID, T2), ca2_slots(ID, S) } > Max.

:- ca2_param(ID, type, hard), ca2_param(ID, max, Max), ca2_param(ID, mode1, "A"), ca2_teams1(ID, T1),
   #count { T2, S : schedule(T2, T1, S), ca2_teams2(ID, T2), ca2_slots(ID, S) } > Max.

:- ca2_param(ID, type, hard), ca2_param(ID, max, Max), ca2_param(ID, mode1, "HA"), ca2_teams1(ID, T1),
   #count { T2, S : schedule(T1, T2, S), ca2_teams2(ID, T2), ca2_slots(ID, S) ;
            T2, S : schedule(T2, T1, S), ca2_teams2(ID, T2), ca2_slots(ID, S) } > Max.


% --- Constraint CA3: Capacity on Consecutive Games ---
% Forbids more than MAX consecutive home/away games for a team.
:- ca3_param(ID, type, hard), ca3_param(ID, max, Max), ca3_param(ID, mode1, "H"), ca3_param(ID, intp, I), ca3_teams1(ID, T),
   Max + 1 { schedule(T, _, S) : slot(S), S >= S0, S < S0 + I }, slot(S0).

:- ca3_param(ID, type, hard), ca3_param(ID, max, Max), ca3_param(ID, mode1, "A"), ca3_param(ID, intp, I), ca3_teams1(ID, T),
   Max + 1 { schedule(_, T, S) : slot(S), S >= S0, S < S0 + I }, slot(S0).


% --- Constraint CA4: Capacity on a Group of Teams ---
% Forbids a group of teams (teams1) from playing more than MAX games against another group (teams2) in a set of slots. 
%Mode "EVERY" applies the check to each slot individually.
:- ca4_param(ID, type, hard), ca4_param(ID, max, Max), ca4_param(ID, mode2, "EVERY"), ca4_slots(ID, Slot),
   #count { T1, T2 : schedule(T1, T2, Slot), ca4_teams1(ID, T1), ca4_teams2(ID, T2) } > Max.

% Mode "GLOBAL" applies the check to the sum over all slots.
:- ca4_param(ID, type, hard), ca4_param(ID, max, Max), ca4_param(ID, mode2, "GLOBAL"),
   #count { T1, T2, S : schedule(T1, T2, S), ca4_teams1(ID, T1), ca4_teams2(ID, T2), ca4_slots(ID, S) } > Max.


% --- Constraint GA1: Game Constraints ---
% Enforces min/max number of specific games in a set of slots.
:- ga1_param(ID, type, hard), ga1_param(ID, min, Min),
   #count { T1, T2, S : schedule(T1, T2, S), ga1_meetings(ID, T1, T2), ga1_slots(ID, S) } < Min.

:- ga1_param(ID, type, hard), ga1_param(ID, max, Max),
   #count { T1, T2, S : schedule(T1, T2, S), ga1_meetings(ID, T1, T2), ga1_slots(ID, S) } > Max.


% --- Constraint BR1: Break Constraints (per team) ---
% Limits the number of breaks for a specific team over a set of slots.
:- br1_param(ID, type, hard), br1_param(ID, intp, MaxBreaks), br1_teams(ID, Team),
   #count{ S : is_break(Team, S), br1_slots(ID, S) } > MaxBreaks.


% --- Constraint BR2: Break Constraints (global) ---
% Limits the total number of breaks for a group of teams over a set of slots.
:- br2_param(ID, type, hard), br2_param(ID, intp, MaxBreaks),
   #count{ T, S : is_break(T, S), br2_teams(ID, T), br2_slots(ID, S) } > MaxBreaks.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Part 3: Soft Constraint Definitions and Objective Function
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- Soft Constraint FA2: Fairness ---
% At any point in time (slot), the difference in home games played between any
% two teams should not be more than `intp`.
home_games_upto(T, S, N) :- team(T), slot(S), N = #count{ S2 : schedule(T, _, S2), S2 <= S }.
diff_at_slot(ID, T1, T2, S, |N1-N2|) :-
    fa2_teams(ID, T1), fa2_teams(ID, T2), T1 < T2,
    fa2_slots(ID, S),
    home_games_upto(T1, S, N1),
    home_games_upto(T2, S, N2).
penalty("FA2", (ID, T1, T2, S), P) :-
    fa2_param(ID, type, soft), fa2_param(ID, intp, I), fa2_param(ID, penalty, P),
    diff_at_slot(ID, T1, T2, S, Diff),
    Diff > I.

% --- Soft Constraint SE1: Separation ---
% The two games between the same pair of opponents should be separated by a minimum number of slots.
penalty("SE1", (ID, T1, T2), (Min - (S2 - S1 - 1)) * P) :-
    se1_param(ID, type, soft), se1_param(ID, min, Min), se1_param(ID, penalty, P),
    se1_teams(ID, T1), se1_teams(ID, T2), T1 < T2,
    schedule(T1, T2, S1), schedule(T2, T1, S2), S1 < S2,
    (S2 - S1 - 1) < Min.

% --- Soft Constraint CA1 ---
penalty("CA1", (ID, Team), (N-Max)*P) :-
    ca1_param(ID, type, soft), ca1_param(ID, max, Max), ca1_param(ID, mode, "H"), ca1_param(ID, penalty, P), ca1_teams(ID, Team),
    N = #count{ Slot : schedule(Team, _, Slot), ca1_slots(ID, Slot) }, N > Max.
penalty("CA1", (ID, Team), (N-Max)*P) :-
    ca1_param(ID, type, soft), ca1_param(ID, max, Max), ca1_param(ID, mode, "A"), ca1_param(ID, penalty, P), ca1_teams(ID, Team),
    N = #count{ Slot : schedule(_, Team, Slot), ca1_slots(ID, Slot) }, N > Max.

% --- Soft Constraint CA2 ---
penalty("CA2", (ID, T1), (N-Max)*P) :-
    ca2_param(ID, type, soft), ca2_param(ID, max, Max), ca2_param(ID, mode1, "H"), ca2_param(ID, penalty, P), ca2_teams1(ID, T1),
    N = #count{ T2, S : schedule(T1, T2, S), ca2_teams2(ID, T2), ca2_slots(ID, S) }, N > Max.
penalty("CA2", (ID, T1), (N-Max)*P) :-
    ca2_param(ID, type, soft), ca2_param(ID, max, Max), ca2_param(ID, mode1, "A"), ca2_param(ID, penalty, P), ca2_teams1(ID, T1),
    N = #count{ T2, S : schedule(T2, T1, S), ca2_teams2(ID, T2), ca2_slots(ID, S) }, N > Max.
penalty("CA2", (ID, T1), (N-Max)*P) :-
    ca2_param(ID, type, soft), ca2_param(ID, max, Max), ca2_param(ID, mode1, "HA"), ca2_param(ID, penalty, P), ca2_teams1(ID, T1),
    N = #count{ T2, S : schedule(T1, T2, S), ca2_teams2(ID, T2), ca2_slots(ID, S) ;
                 T2, S : schedule(T2, T1, S), ca2_teams2(ID, T2), ca2_slots(ID, S) }, N > Max.

% --- Soft Constraint CA3 ---
violated_ca3(ID, T, S0, N) :-
    ca3_param(ID, type, soft), ca3_param(ID, mode1, "H"), ca3_teams1(ID, T), ca3_param(ID, intp, I), slot(S0),
    N = #count{ J : J=0..I-1, schedule(T, _, S0+J) }.
violated_ca3(ID, T, S0, N) :-
    ca3_param(ID, type, soft), ca3_param(ID, mode1, "A"), ca3_teams1(ID, T), ca3_param(ID, intp, I), slot(S0),
    N = #count{ J : J=0..I-1, schedule(_, T, S0+J) }.
penalty("CA3", (ID, T, S0), (N-Max)*P) :-
    violated_ca3(ID, T, S0, N), ca3_param(ID, max, Max), ca3_param(ID, penalty, P), N > Max.

% --- Soft Constraint CA4 ---
penalty("CA4", (ID, Slot), (N-Max)*P) :-
    ca4_param(ID, type, soft), ca4_param(ID, max, Max), ca4_param(ID, mode2, "EVERY"), ca4_param(ID, penalty, P), ca4_slots(ID, Slot),
    N = #count{ T1, T2 : schedule(T1, T2, Slot), ca4_teams1(ID, T1), ca4_teams2(ID, T2) }, N > Max.
penalty("CA4", (ID, "GLOBAL"), (N-Max)*P) :-
    ca4_param(ID, type, soft), ca4_param(ID, max, Max), ca4_param(ID, mode2, "GLOBAL"), ca4_param(ID, penalty, P),
    N = #count{ T1, T2, S : schedule(T1, T2, S), ca4_teams1(ID, T1), ca4_teams2(ID, T2), ca4_slots(ID, S) }, N > Max.

% --- Soft Constraint GA1 ---
penalty("GA1_min", ID, (Min-N)*P) :-
    ga1_param(ID, type, soft), ga1_param(ID, min, Min), ga1_param(ID, penalty, P),
    N = #count{ T1, T2, S : schedule(T1, T2, S), ga1_meetings(ID, T1, T2), ga1_slots(ID, S) }, N < Min.
penalty("GA1_max", ID, (N-Max)*P) :-
    ga1_param(ID, type, soft), ga1_param(ID, max, Max), ga1_param(ID, penalty, P),
    N = #count{ T1, T2, S : schedule(T1, T2, S), ga1_meetings(ID, T1, T2), ga1_slots(ID, S) }, N > Max.

% --- Soft Constraint BR1 & BR2: Breaks ---
penalty("BR1", ID, (N-MaxBreaks)*P) :-
    br1_param(ID, type, soft), br1_param(ID, intp, MaxBreaks), br1_param(ID, penalty, P), br1_teams(ID, Team),
    N = #count{ S : is_break(Team, S), br1_slots(ID, S) }, N > MaxBreaks.
penalty("BR2", ID, (N-MaxBreaks)*P) :-
    br2_param(ID, type, soft), br2_param(ID, intp, MaxBreaks), br2_param(ID, penalty, P),
    N = #count{ T, S : is_break(T, S), br2_teams(ID, T), br2_slots(ID, S) }, N > MaxBreaks.

% --- Objective Function ---
% Minimize the sum of all penalty costs from all violated soft constraints.
#minimize { Cost, Constraint, ViolationID : penalty(Constraint, ViolationID, Cost) }.

#show schedule/3.

