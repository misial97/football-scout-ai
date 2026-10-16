
import pandas as pd

# 1. Cargar los datos originales
df = pd.read_csv("players_data-2025_2026.csv")

print(f"Filas originales: {len(df)}")

# 2. Elegir solo las columnas que necesitamos
columnas = [
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

df = df[columnas].copy()

# 3. Convertir las estadisticas numericas a numeros
numericas = ["Age", "MP", "Min", "Gls", "Ast", "Sh", "SoT"]

for columna in numericas:
    df[columna] = pd.to_numeric(df[columna], errors="coerce")

# 4. Eliminar filas sin informacion esencial
df = df.dropna(subset=["Player", "Pos", "Min"])

# 5. Calcular estadisticas por cada 90 minutos
# Solo calculamos estos indicadores si hay minutos jugados.
df["Gls_90"] = df["Gls"] / df["Min"] * 90
df["Ast_90"] = df["Ast"] / df["Min"] * 90
df["Sh_90"] = df["Sh"] / df["Min"] * 90
df["SoT_90"] = df["SoT"] / df["Min"] * 90

# 6. Guardar la tabla preparada
df.to_csv("players_clean.csv", index=False)

# 7. Comprobar el resultado
print(f"\nFilas tras la limpieza: {len(df)}")
print(f"Columnas finales: {len(df.columns)}")

print("\nEjemplo de jugadores:")
print(
    df[
        ["Player", "Pos", "Min", "Gls", "Gls_90", "Ast_90"]
    ].head(10).to_string(index=False)
)

print("\nArchivo creado: players_clean.csv")
