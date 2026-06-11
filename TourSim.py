"""
simulate_tournament.py
======================
Runs the 2026 FIFA World Cup simulation N times and stores all results.

Outputs
-------
results/
  summary.csv               — champion tally + win %, runner-up tally, SF/QF/R16 appearances
  champions.csv             — one row per run: run_id, champion
  knockout_results.csv      — every knockout match result across all runs
  group_results.csv         — every group-stage match result across all runs
  deep_runs.csv             — per-team, per-run: how far each team reached
  scorelines_group.csv      — frequency of every scoreline in the group stage (all FT)
  scorelines_knockout.csv   — frequency of every scoreline in the knockout stage, split by FT / AET / PENS
  scorelines_all.csv        — combined scoreline frequencies across both stages
"""

import random
import os
import pandas as pd
from itertools import combinations
from collections import defaultdict
from copy import deepcopy

import MatchSim
from Tournament import (
    Match,
    groups,
    generate_group_fixtures,
    group_standings,
    get_best_third_place_teams,
    build_round_of_32,
    random_match,
    team_stats_df,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

N_SIMULATIONS = 100000
RANDOM_SEED    = None   # Set to an int (e.g. 42) for reproducibility; None = random each run
OUTPUT_DIR     = "results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Silent simulation helpers (no stdout printing)
# ---------------------------------------------------------------------------

def simulate_group_stage_silent(group_fixtures):
    for matches in group_fixtures.values():
        for match in matches:
            random_match(match, knockout=False)


def simulate_knockout_silent(r32_matches):
    """
    Run R32 → Final silently.
    Returns a dict mapping round_name → list of Match objects,
    plus 'champion' key with the winning team name.
    """
    round_names = ['Round of 32', 'Round of 16', 'Quarter-finals', 'Semi-finals', 'Final']
    round_results = {}
    current_round = r32_matches

    for round_name in round_names:
        for match in current_round:
            random_match(match, knockout=True)
        round_results[round_name] = list(current_round)

        if len(current_round) == 1:
            round_results['champion'] = current_round[0].winner
            return round_results

        # Build next round
        winners = [m.winner for m in current_round]
        current_round = [Match(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    return round_results  # fallback (shouldn't reach here)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_simulations(n=N_SIMULATIONS, seed=RANDOM_SEED):
    if seed is not None:
        random.seed(seed)

    # Accumulators
    champion_counts   = defaultdict(int)
    runner_up_counts  = defaultdict(int)
    sf_counts         = defaultdict(int)
    qf_counts         = defaultdict(int)
    r16_counts        = defaultdict(int)
    r32_counts        = defaultdict(int)

    # Scoreline counters: key = "X-Y (outcome)" e.g. "2-1 (FT)", "1-1 (AET)", "0-0 (PENS)"
    # Group stage only ever has FT results; knockout can be FT, AET, or PENS.
    scoreline_group    = defaultdict(int)
    scoreline_knockout = defaultdict(int)

    champions_rows       = []
    knockout_rows        = []
    group_rows           = []
    deep_run_rows        = []

    print(f"Running {n} simulations…")

    for run_id in range(1, n + 1):
        if run_id % 10 == 0:
            print(f"  Completed {run_id}/{n}")

        # --- Group stage ---
        group_fixtures = generate_group_fixtures(groups)
        simulate_group_stage_silent(group_fixtures)

        # Store group results
        for group_name, matches in group_fixtures.items():
            for m in matches:
                group_rows.append({
                    'run_id':      run_id,
                    'group':       group_name,
                    'home':        m.home,
                    'away':        m.away,
                    'home_goals':  m.home_goals,
                    'away_goals':  m.away_goals,
                    'winner':      m.winner,
                })
                # Canonical scoreline: higher score first, always FT in group stage
                hi, lo = sorted([m.home_goals, m.away_goals], reverse=True)
                scoreline_group[f"{hi}-{lo} (FT)"] += 1

        # --- Knockout stage ---
        r32 = build_round_of_32(group_fixtures)
        ko_results = simulate_knockout_silent(r32)

        champion = ko_results['champion']
        champion_counts[champion] += 1
        champions_rows.append({'run_id': run_id, 'champion': champion})

        # Determine finalist (runner-up = finalist who lost the final)
        final_match = ko_results['Final'][0]
        runner_up = final_match.away if final_match.winner == final_match.home else final_match.home
        runner_up_counts[runner_up] += 1

        # Track deep-run milestones per team
        round_exit = {}  # team → furthest round label

        round_order = ['Round of 32', 'Round of 16', 'Quarter-finals', 'Semi-finals', 'Final']
        for round_name in round_order:
            for m in ko_results[round_name]:
                # Store match result
                knockout_rows.append({
                    'run_id':      run_id,
                    'round':       round_name,
                    'home':        m.home,
                    'away':        m.away,
                    'home_goals':  m.home_goals,
                    'away_goals':  m.away_goals,
                    'extra_time':  m.extra_time,
                    'penalties':   m.penalties,
                    'winner':      m.winner,
                })
                # Canonical scoreline with outcome type
                hi, lo = sorted([m.home_goals, m.away_goals], reverse=True)
                if m.penalties:
                    outcome = 'PENS'
                elif m.extra_time:
                    outcome = 'AET'
                else:
                    outcome = 'FT'
                scoreline_knockout[f"{hi}-{lo} ({outcome})"] += 1
                # Loser's furthest round = this round
                loser = m.away if m.winner == m.home else m.home
                round_exit[loser] = round_name

        # Champion's furthest round = 'Winner'
        round_exit[champion] = 'Winner'

        # Count appearances by round
        for team, reached in round_exit.items():
            if reached in ('Semi-finals', 'Final', 'Winner'):
                sf_counts[team] += 1
            if reached in ('Quarter-finals', 'Semi-finals', 'Final', 'Winner'):
                qf_counts[team] += 1
            if reached in ('Round of 16', 'Quarter-finals', 'Semi-finals', 'Final', 'Winner'):
                r16_counts[team] += 1
            r32_counts[team] += 1

        for team, reached in round_exit.items():
            deep_run_rows.append({'run_id': run_id, 'team': team, 'furthest_round': reached})

    # ---------------------------------------------------------------------------
    # Build summary DataFrame
    # ---------------------------------------------------------------------------
    all_teams = sorted(set(
        team for g in groups.values() for team in g
    ))

    summary_rows = []
    for team in all_teams:
        wins    = champion_counts[team]
        ru      = runner_up_counts[team]
        sf      = sf_counts[team]
        qf      = qf_counts[team]
        r16     = r16_counts[team]
        summary_rows.append({
            'team':             team,
            'titles':           wins,
            'title_%':          round(wins / n * 100, 1),
            'runner_up':        ru,
            'final_%':          round((wins + ru) / n * 100, 1),
            'semi_finals':      sf,
            'sf_%':             round(sf / n * 100, 1),
            'quarter_finals':   qf,
            'qf_%':             round(qf / n * 100, 1),
            'round_of_16':      r16,
            'r16_%':            round(r16 / n * 100, 1),
        })

    summary_df = (
        pd.DataFrame(summary_rows)
        .sort_values(['titles', 'runner_up', 'semi_finals'], ascending=False)
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------------------------
    # Build scoreline frequency DataFrames
    # ---------------------------------------------------------------------------

    def scoreline_df(counter, total_matches):
        rows = []
        for key, count in counter.items():
            # Key format: "X-Y (OUTCOME)"
            score_part, outcome_part = key.rsplit(' ', 1)
            hi, lo = map(int, score_part.split('-'))
            outcome = outcome_part.strip('()')
            rows.append({
                'scoreline':    score_part,
                'outcome':      outcome,
                'higher_score': hi,
                'lower_score':  lo,
                'count':        count,
                'frequency_%':  round(count / total_matches * 100, 2),
            })
        return (
            pd.DataFrame(rows)
            .sort_values(['count', 'higher_score', 'lower_score'], ascending=[False, True, True])
            .reset_index(drop=True)
        )

    # Total matches per stage across all runs
    # Group stage: 6 matches per group × 12 groups × n runs
    total_group_matches    = 6 * 12 * n
    # Knockout: 16 + 8 + 4 + 2 + 1 = 31 matches per run
    total_knockout_matches = 31 * n

    sl_group_df    = scoreline_df(scoreline_group,    total_group_matches)
    sl_knockout_df = scoreline_df(scoreline_knockout, total_knockout_matches)

    # Combined (merge on scoreline, sum counts)
    all_scores = defaultdict(int)
    for k, v in scoreline_group.items():
        all_scores[k] += v
    for k, v in scoreline_knockout.items():
        all_scores[k] += v
    sl_all_df = scoreline_df(all_scores, total_group_matches + total_knockout_matches)

    # ---------------------------------------------------------------------------
    # Save all outputs
    # ---------------------------------------------------------------------------
    summary_df.to_csv(f"{OUTPUT_DIR}/summary.csv", index=False)
    pd.DataFrame(champions_rows).to_csv(f"{OUTPUT_DIR}/champions.csv", index=False)
    pd.DataFrame(knockout_rows).to_csv(f"{OUTPUT_DIR}/knockout_results.csv", index=False)
    pd.DataFrame(group_rows).to_csv(f"{OUTPUT_DIR}/group_results.csv", index=False)
    pd.DataFrame(deep_run_rows).to_csv(f"{OUTPUT_DIR}/deep_runs.csv", index=False)
    sl_group_df.to_csv(f"{OUTPUT_DIR}/scorelines_group.csv", index=False)
    sl_knockout_df.to_csv(f"{OUTPUT_DIR}/scorelines_knockout.csv", index=False)
    sl_all_df.to_csv(f"{OUTPUT_DIR}/scorelines_all.csv", index=False)

    print(f"\nDone! Results saved to '{OUTPUT_DIR}/'")
    print("\n=== TOP 10 TITLE CONTENDERS ===")
    print(summary_df[['team', 'titles', 'title_%', 'runner_up', 'semi_finals']].head(10).to_string(index=False))
    print("\n=== TOP 10 MOST COMMON SCORELINES (all matches) ===")
    print(sl_all_df[['scoreline', 'outcome', 'count', 'frequency_%']].head(10).to_string(index=False))

    return summary_df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_simulations()