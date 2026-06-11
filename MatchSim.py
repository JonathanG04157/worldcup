import numpy as np
from scipy.stats import poisson
import random

def expected_goals(attack_team, defence_team):

    BASE_GOALS = 1.2   # average goals per team per game in international football, assumed 90 mins

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

    home_goals = np.random.poisson(lambda_home)
    away_goals = np.random.poisson(lambda_away)
    return {'home_goals': home_goals, 'away_goals': away_goals}

def simulate_knockout_match(match, team_stats): #knockout stage (determined by extra time, then pens)
    home = team_stats[match.home]
    away = team_stats[match.away]

    extra_time = False
    penalties = False

    lambda_home = expected_goals(attack_team = home, defence_team = away)
    lambda_away = expected_goals(attack_team = away, defence_team = home)

    home_goals = np.random.poisson(lambda_home)
    away_goals = np.random.poisson(lambda_away)

    if home_goals == away_goals:
        # Extra time: add a small number of extra goals
        extra_time = True
        extra_home = np.random.poisson(lambda_home * 0.3)  # ~30% of 90min rate
        extra_away = np.random.poisson(lambda_away * 0.3)
        home_goals += extra_home
        away_goals += extra_away

    # If still level, penalties — slight benefit to better team (per FIFA rankings)
    if home_goals == away_goals:
        penalties = True
        ranking_benefit = 0.1*(home['Points'] - away['Points'])/(1877.27 - 1275.58)
        
        # Scales between -0.1 and +0.1, depening on the difference of the two teams, as a fraction of maximum difference
        # Maximum difference would be New Zealand vs. Argentina
        #Positive for home benefit, negative for away benefit
        
        if random.random() < 0.5 + ranking_benefit:
            home_goals += 1
        else:
            away_goals += 1

    return {'home_goals': home_goals, 'away_goals': away_goals, 'is_ET': extra_time, 'is_PEN': penalties}
