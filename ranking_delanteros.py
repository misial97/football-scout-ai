
import pandas as pd

df = pd.read_csv("players_clean.csv")

MINIMUM_MINUTES = 900

# 1. Select forwards, including mixed positions
forwards = df[
    df["Pos"].fillna("").str.split(",").apply(
        lambda player_positions: "FW" in player_positions
    )
].copy()

# 2. Filter by participation
forwards = forwards[
    forwards["Min"] >= MINIMUM_MINUTES
].copy()

# 3. Calculate shot accuracy
# Leave the value empty when a player has no shots.
forwards["Shot_accuracy"] = (
    forwards["SoT"]
    .div(forwards["Sh"].where(forwards["Sh"] > 0))
)

# 4. Convert each indicator to a percentile between 0 and 1.
# A value of 0.90 means it is approximately above 90% of candidates.
indicators = {
    "Gls_90": 0.50,
    "Ast_90": 0.20,
    "SoT_90": 0.20,
    "Shot_accuracy": 0.10,
}

for column in indicators:
    forwards[f"{column}_percentile"] = (
        forwards[column].rank(pct=True)
    )

# 5. Calculate a weighted score from 0 to 100
forwards["Score"] = 0

for column, weight in indicators.items():
    percentile = forwards[f"{column}_percentile"].fillna(0)
    forwards["Score"] += percentile * weight * 100

# 6. Sort by the new score
ranking = forwards.sort_values(
    by="Score",
    ascending=False
)

output_columns = [
    "Player",
    "Squad",
    "Pos",
    "Min",
    "Gls",
    "Ast",
    "Gls_90",
    "Ast_90",
    "SoT_90",
    "Shot_accuracy",
    "Score",
]

print(f"Candidates analyzed: {len(ranking)}")
print("\nTop 15 by combined score:")
print(
    ranking[output_columns]
    .head(15)
    .round(3)
    .to_string(index=False)
)

ranking[output_columns].to_csv(
    "ranking_delanteros.csv",
    index=False
)

print("\nUpdated file: ranking_delanteros.csv")
