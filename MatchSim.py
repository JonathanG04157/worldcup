import numpy as np
from scipy.stats import poisson


BASE_GOALS = 1.2   # average goals per team per game in international football

def expected_goals(attack_team, defence_team):
    """
    Expected goals = base rate * attacker strength * (1 / defender strength)
    defender strength > 1 means weak defence (concedes more)
    defender strength < 1 means strong defence
    """
    return BASE_GOALS * attack_team['attack'] * defence_team['defence']

def simulate_match_poisson(match, team_stats):
    home = team_stats[match.home]
    away = team_stats[match.away]

    lambda_home = expected_goals(home, away)
    lambda_away = expected_goals(away, home)

    match.home_goals = np.random.poisson(lambda_home)
    match.away_goals = np.random.poisson(lambda_away)

def simulate_knockout_match(match, team_stats):
    simulate_match_poisson(match, team_stats)

    if match.home_goals == match.away_goals:
        # Extra time: add a small number of extra goals
        extra_home = np.random.poisson(lambda_home * 0.3)  # ~30% of 90min rate
        extra_away = np.random.poisson(lambda_away * 0.3)
        match.home_goals += extra_home
        match.away_goals += extra_away

    # If still level, penalties — effectively a coin flip with slight home edge
    if match.home_goals == match.away_goals:
        if random.random() < 0.5:
            match.home_goals += 1
        else:
            match.away_goals += 1

# Simplified version: use FIFA ranking points as a proxy
# Real FIFA points range roughly 1400-1800 for top nations

def rating_to_strength(rating, max_rating=1877.27, base=1.0):
    """Scales a FIFA rating to a multiplier around 1.0."""
    return base + (rating - 1500) / 1000   # linear scaling

team_stats = {
    team: {
        'attack':  rating_to_strength(rating),
        'defence': 2.0 - rating_to_strength(rating)  # stronger team = better defence
    }
    for team, rating in fifa_rankings.items()
}