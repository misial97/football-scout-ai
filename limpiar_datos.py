
import pandas as pd

# 1. Load the original data
df = pd.read_csv("players_data-2025_2026.csv")

print(f"Original rows: {len(df)}")

# 2. Keep only the columns we need
selected_columns = [
    "Player",
    "Nation",
    "Pos",
    "Squad",
    "Comp",
    "Age",
    "MP",
    "Min",
    "Gls",
    "Ast",
    "Sh",
    "SoT",
]

df = df[selected_columns].copy()

# 3. Convert numeric statistics to numbers
numeric_columns = ["Age", "MP", "Min", "Gls", "Ast", "Sh", "SoT"]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# 4. Remove rows without essential information or goalkeeper records
df = df.dropna(subset=["Player", "Pos", "Min"])
df = df[
    ~df["Pos"].str.split(",").apply(lambda positions: "GK" in positions)
].copy()

# 5. Calculate statistics per 90 minutes
# Only calculate these indicators when minutes have been played.
df["Gls_90"] = df["Gls"] / df["Min"] * 90
df["Ast_90"] = df["Ast"] / df["Min"] * 90
df["Sh_90"] = df["Sh"] / df["Min"] * 90
df["SoT_90"] = df["SoT"] / df["Min"] * 90

# 6. Save the prepared table
df.to_csv("players_clean.csv", index=False)

# 7. Check the result
print(f"\nRows after cleaning: {len(df)}")
print(f"Final columns: {len(df.columns)}")

print("\nExample players:")
print(
    df[
        ["Player", "Pos", "Min", "Gls", "Gls_90", "Ast_90"]
    ].head(10).to_string(index=False)
)

print("\nCreated file: players_clean.csv")
