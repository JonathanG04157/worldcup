import pandas as pd

def rating_to_strength(rating, base=1.0):
    return base + (rating - 1500) / 1000

team_stats = {
    team: {
        'attack':  rating_to_strength(rating),
        'defence': 2.0 - rating_to_strength(rating)
    }
    for team, rating in fifa_rankings.items()
}

df = pd.read_csv('/Users/benjaminjordan/Documents/World Cup Model/worldcup/team_rankings.csv')

# Build the rankings dict and team_stats in two lines
fifa_rankings = dict(zip(df['Team'], df['Points']))

team_stats = {
    team: {
        'attack':  rating_to_strength(rating),
        'defence': 2.0 - rating_to_strength(rating)
    }
    for team, rating in fifa_rankings.items()
}

df['attack']  = df['Points'].apply(rating_to_strength)
df['defence'] = df['Points'].apply(lambda r: 2.0 - rating_to_strength(r))

print(df.to_string(index=False))