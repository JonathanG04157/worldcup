from dataclasses import dataclass, field
from typing import Optional
from itertools import combinations
import random
import MatchSim
import pandas as pd

team_stats_df = pd.read_csv("team_stats.csv")

@dataclass
class Match:
    home: str
    away: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    extra_time: bool = False
    penalties: bool = False

    @property
    def result(self):
        if self.home_goals is None:
            return f"{self.home} vs {self.away} - Not played"
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


# ---------------------------------------------------------------------------
# All 12 groups — 2026 World Cup (USA / Canada / Mexico)
# ---------------------------------------------------------------------------

groups = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czechia'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['USA', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curacao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Iraq', 'Norway'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}


# ---------------------------------------------------------------------------
# Group stage
# ---------------------------------------------------------------------------

def generate_group_fixtures(groups):
    """Create all round-robin matchups within each group."""
    return {
        name: [Match(h, a) for h, a in combinations(teams, 2)]
        for name, teams in groups.items()
    }


def group_standings(teams, matches):
    """
    Return the group table sorted by points, then goal difference, then goals scored.
    Each entry is (team_name, stats_dict).
    """
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

    return sorted(
        table.items(),
        key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga'], x[1]['gf']),
        reverse=True,
    )


def print_group_standings(group_name, teams, matches):
    print(f"\n  Group {group_name} standings:")
    print(f"  {'Team':<28} Pts  GF  GA  GD")
    print(f"  {'-'*50}")
    for i, (team, stats) in enumerate(group_standings(teams, matches)):
        gd = stats['gf'] - stats['ga']
        marker = "✓" if i < 2 else " "  # top 2 auto-qualify
        print(f"  {marker} {team:<27}  {stats['pts']:>2}  {stats['gf']:>2}  {stats['ga']:>2}  {gd:>+3}")


# ---------------------------------------------------------------------------
# Third-place qualification
# ---------------------------------------------------------------------------

def get_best_third_place_teams(group_fixtures, n=8):
    """
    Collect the third-placed team from each group, rank them, and return the
    best n (the 2026 format sends the top 8 third-place teams through).
    """
    third_place = []
    for group_name, matches in group_fixtures.items():
        standings = group_standings(groups[group_name], matches)
        team, stats = standings[2]
        third_place.append((team, stats, group_name))

    # Sort by points, then goal difference, then goals scored
    third_place.sort(
        key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga'], x[1]['gf']),
        reverse=True,
    )
    return [t[0] for t in third_place[:n]]


# ---------------------------------------------------------------------------
# Knockout bracket — Round of 32
#
# The official 2026 bracket is complex (third-place slots depend on which
# groups they came from). This implementation uses the real group-winner /
# runner-up pairings and fills the third-place slots in ranked order.
# ---------------------------------------------------------------------------

def build_round_of_32(group_fixtures):
    """
    Build the Round of 32 using the official 2026 FIFA bracket structure.
    Returns a list of 16 Match objects.
    """
    q = {}  # qualifiers: q[group][1] = winner, q[group][2] = runner-up
    for g, matches in group_fixtures.items():
        standings = group_standings(groups[g], matches)
        q[g] = {1: standings[0][0], 2: standings[1][0]}

    best_thirds = get_best_third_place_teams(group_fixtures, n=8)
    t = best_thirds  # t[0] is best third, t[7] is 8th best

    # Official 2026 R32 pairings (simplified — thirds slotted by rank)
    r32 = [
        Match(q['A'][2], q['B'][2]),
        Match(q['C'][1], q['F'][2]),
        Match(q['E'][1], t[0]),
        Match(q['F'][1], q['C'][2]),
        Match(q['E'][2], q['I'][2]),
        Match(q['I'][1], t[1]),
        Match(q['A'][1], t[2]),
        Match(q['L'][1], t[3]),
        Match(q['G'][1], t[4]),
        Match(q['D'][1], t[5]),
        Match(q['H'][1], q['J'][2]),
        Match(q['K'][2], q['L'][2]),
        Match(q['B'][1], t[6]),
        Match(q['D'][2], q['G'][2]),
        Match(q['J'][1], q['H'][2]),
        Match(q['K'][1], t[7]),
    ]
    return r32


# ---------------------------------------------------------------------------
# Knockout progression
# ---------------------------------------------------------------------------

def advance_round(matches):
    """Pair consecutive winners to form the next round's fixtures."""
    winners = [m.winner for m in matches]
    return [Match(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]


# ---------------------------------------------------------------------------
# Match simulation
# ---------------------------------------------------------------------------

def random_match(match, knockout=False, team_stats = team_stats_df):

    if knockout:
        result = MatchSim.simulate_knockout_match(match, team_stats)
        match.home_goals = result['home_goals']
        match.away_goals = result['away_goals']
        match.extra_time = result['is_ET']
        match.penalties = result['is_PEN']

    else:
        result = MatchSim.simulate_match_poisson(match, team_stats)
        match.home_goals = result['home_goals']
        match.away_goals = result['away_goals']



# ---------------------------------------------------------------------------
# Tournament runner
# ---------------------------------------------------------------------------

def simulate_group_stage(group_fixtures, simulate_fn):
    print("=" * 55)
    print("  GROUP STAGE — 2026 FIFA World Cup")
    print("=" * 55)
    for group_name, matches in group_fixtures.items():
        for match in matches:
            simulate_fn(match, knockout=False, team_stats = team_stats_df) #added team_stats influence here
        print_group_standings(group_name, groups[group_name], matches)

    print("\n  ✓ = automatic qualifier (top 2)")


def simulate_knockout(r32_matches, simulate_fn):
    """Run R32 → R16 → QF → SF → Final."""
    round_names = [
        'Round of 32',
        'Round of 16',
        'Quarter-finals',
        'Semi-finals',
        'Final',
    ]
    current_round = r32_matches

    print("\n" + "=" * 55)
    print("  KNOCKOUT STAGE")
    print("=" * 55)

    for round_name in round_names:
        print(f"\n  --- {round_name} ---")
        for match in current_round:
            simulate_fn(match, knockout=True, team_stats = team_stats_df) #added team_stats influence here
            print(f"    {match.result}")

        if len(current_round) == 1:
            print(f"\n  🏆 Champion: {current_round[0].winner}")
            return current_round[0].winner

        current_round = advance_round(current_round)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(42)  # Change or remove for different results each run

    group_fixtures = generate_group_fixtures(groups)
    simulate_group_stage(group_fixtures, random_match)

    r32 = build_round_of_32(group_fixtures)
    simulate_knockout(r32, random_match)