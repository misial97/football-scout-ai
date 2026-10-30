
import pandas as pd

# 1. Load the CSV file
df = pd.read_csv("players_data-2025_2026.csv")

# 2. Display the table dimensions
print("Rows and columns:")
print(df.shape)

# 3. Display the column names
print("\nAvailable columns:")
print(df.columns.tolist())

# 4. Display the first five players
print("\nFirst five players:")
print(df[["Player", "Pos", "Squad", "Min", "Gls", "Ast"]].head())

# 5. Check missing data
print("\nMissing values by column:")
print(df.isna().sum().sort_values(ascending=False).head(10))

# 6. General summary
print("\nStatistical summary:")
print(df[["Age", "Min", "Gls", "Ast"]].describe())


# 7. Count players by position
print("\nPlayers by position:")
print(df["Pos"].value_counts(dropna=False))

# 8. Check duplicate players
print("\nCompletely duplicated rows:")
print(df.duplicated().sum())

print("\nDuplicated player names:")
print(df["Player"].duplicated().sum())

# 9. Percentage of missing values by column
print("\nColumns with more than 50% missing data:")
missing_percentages = df.isna().mean() * 100

print(
    missing_percentages[missing_percentages > 50]
    .sort_values(ascending=False)
    .round(1)
    .astype(str) + "%"
)

# 10. Check minutes and goals
print("\nMinutes and goals summary:")
print(df[["Min", "90s", "Gls", "Ast"]].describe())
