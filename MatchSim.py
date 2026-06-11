import numpy as np
from scipy.stats import poisson
import random


BASE_GOALS = 1.2   # average goals per team per game in international football, assumed 90 mins

def expected_goals(attack_team, defence_team):
    """
    Expected goals = base rate * attacker strength * defender strength
    defender strength > 1 means weak defence (concedes more)
    defender strength < 1 means strong defence
    """
    return BASE_GOALS * attack_team['attack'] * defence_team['defence']

# match = pair of teams, so-called home and away

def simulate_match_poisson(match, team_stats): #group stage (draws allowed)
    home = team_stats[match.home]
    away = team_stats[match.away]

    lambda_home = expected_goals(attack_team = home, defence_team = away)
    lambda_away = expected_goals(attack_team = away, defence_team = home)

    match.home_goals = np.random.poisson(lambda_home)
    match.away_goals = np.random.poisson(lambda_away)

def simulate_knockout_match(match, team_stats): #knockout stage (determined by extra time, then pens)
    home = team_stats[match.home]
    away = team_stats[match.away]

    lambda_home = expected_goals(attack_team = home, defence_team = away)
    lambda_away = expected_goals(attack_team = away, defence_team = home)

    match.home_goals = np.random.poisson(lambda_home)
    match.away_goals = np.random.poisson(lambda_away)

    if match.home_goals == match.away_goals:
        # Extra time: add a small number of extra goals
        match.extra_time = True
        extra_home = np.random.poisson(lambda_home * 0.3)  # ~30% of 90min rate
        extra_away = np.random.poisson(lambda_away * 0.3)
        match.home_goals += extra_home
        match.away_goals += extra_away

    # If still level, penalties — effectively a coin 
    if match.home_goals == match.away_goals:
        match.penalties = True
        if random.random() < 0.5:
            match.home_goals += 1
        else:
            match.away_goals += 1
