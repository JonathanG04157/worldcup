from dataclasses import dataclass
from typing import Optional

@dataclass
class Match:
    home: str
    away: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None

    @property
    def result(self):
        if self.home_goals is None:
            return "Not played"
        return f"{self.home} {self.home_goals} - {self.away_goals} {self.away}"

    @property
    def winner(self):
        if self.home_goals is None:
            return None
        if self.home_goals > self.away_goals:
            return self.home
        elif self.away_goals > self.home_goals:
            return self.away
        return "Draw"
    
from itertools import combinations

groups = {
    'A': ['Qatar', 'Ecuador', 'Senegal', 'Netherlands'],
    'B': ['England', 'Iran', 'USA', 'Wales'],
    'C': ['Argentina', 'Saudi Arabia', 'Mexico', 'Poland'],
    # ... etc
}

def generate_group_fixtures(groups):
    fixtures = {}
    for group_name, teams in groups.items():
        # combinations gives every unique pair: (A,B), (A,C), (A,D), (B,C), (B,D), (C,D)
        fixtures[group_name] = [Match(home, away) for home, away in combinations(teams, 2)]
    return fixtures

group_fixtures = generate_group_fixtures(groups)

# See group A's matches:
for match in group_fixtures['A']:
    print(match.result)
# Qatar vs Ecuador - Not played
# Qatar vs Senegal - Not played
# ...


def group_standings(teams, matches):
    table = {team: {'pts': 0, 'gf': 0, 'ga': 0} for team in teams}

    for m in matches:
        if m.home_goals is None:
            continue
        table[m.home]['gf'] += m.home_goals
        table[m.home]['ga'] += m.away_goals
        table[m.away]['gf'] += m.away_goals
        table[m.away]['ga'] += m.home_goals

        if m.home_goals > m.away_goals:
            table[m.home]['pts'] += 3
        elif m.away_goals > m.home_goals:
            table[m.away]['pts'] += 3
        else:
            table[m.home]['pts'] += 1
            table[m.away]['pts'] += 1

    # Sort by points, then goal difference
    return sorted(
        table.items(),
        key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga']),
        reverse=True
    )

def build_knockout_bracket(group_results):
    """
    Takes the top 2 from each group and builds the R16.
    World Cup R16 matchups: 1A v 2B, 1C v 2D, 1E v 2F, 1G v 2H
                            1B v 2A, 1D v 2C, 1F v 2E, 1H v 2G
    """
    # Get top 2 from each group
    qualifiers = {}
    for group_name, matches in group_results.items():
        standings = group_standings(groups[group_name], matches)
        qualifiers[group_name] = {
            1: standings[0][0],  # group winner
            2: standings[1][0]   # runner up
        }

    r16 = [
        Match(qualifiers['A'][1], qualifiers['B'][2]),
        Match(qualifiers['C'][1], qualifiers['D'][2]),
        Match(qualifiers['E'][1], qualifiers['F'][2]),
        Match(qualifiers['G'][1], qualifiers['H'][2]),
        Match(qualifiers['B'][1], qualifiers['A'][2]),
        Match(qualifiers['D'][1], qualifiers['C'][2]),
        Match(qualifiers['F'][1], qualifiers['E'][2]),
        Match(qualifiers['H'][1], qualifiers['G'][2]),
    ]
    return r16


def advance_round(matches):
    """Takes a list of played matches and returns the next round's fixtures."""
    winners = [m.winner for m in matches]
    # Pair winners: match 0 winner vs match 1 winner, etc.
    next_round = []
    for i in range(0, len(winners), 2):
        next_round.append(Match(winners[i], winners[i+1]))
    return next_round


def simulate_knockout(r16_matches, simulate_match_fn):
    """Runs through all knockout rounds to produce a winner."""
    rounds = ['Round of 16', 'Quarter-finals', 'Semi-finals', 'Final']
    current_round = r16_matches

    for round_name in rounds:
        print(f"\n--- {round_name} ---")
        for match in current_round:
            simulate_match_fn(match)   # your model fills in the scores
            print(match.result)
        if len(current_round) > 1:
            current_round = advance_round(current_round)
        else:
            print(f"\n🏆 Winner: {current_round[0].winner}")

import random

def simple_random_match(match):
    """Placeholder — swap this for your real model later."""
    match.home_goals = random.randint(0, 3)
    match.away_goals = random.randint(0, 3)
    # In knockouts, no draws — add extra time logic here

group_fixtures = generate_group_fixtures(groups)

# Simulate group stage
for group_name, matches in group_fixtures.items():
    for match in matches:
        simple_random_match(match)

# Build and run knockouts
r16 = build_knockout_bracket(group_fixtures)
simulate_knockout(r16, simple_random_match)