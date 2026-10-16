
import pandas as pd

df = pd.read_csv("players_clean.csv")

MINUTOS_MINIMOS = 900

# 1. Seleccionar delanteros, incluyendo posiciones mixtas
delanteros = df[
    df["Pos"].fillna("").str.split(",").apply(
        lambda posiciones: "FW" in posiciones
    )
].copy()

# 2. Filtrar por participacion
delanteros = delanteros[
    delanteros["Min"] >= MINUTOS_MINIMOS
].copy()

# 3. Calcular precision de tiro
# Si un jugador no ha realizado tiros, dejamos el valor vacio.
delanteros["Precision_tiro"] = (
    delanteros["SoT"]
    .div(delanteros["Sh"].where(delanteros["Sh"] > 0))
)

# 4. Convertir cada indicador en un percentil entre 0 y 1.
# Un valor de 0.90 significa que supera aproximadamente
# al 90% de los candidatos en ese indicador.
indicadores = {
    "Gls_90": 0.50,
    "Ast_90": 0.20,
    "SoT_90": 0.20,
    "Precision_tiro": 0.10,
}

for columna in indicadores:
    delanteros[f"{columna}_percentil"] = (
        delanteros[columna].rank(pct=True)
    )

# 5. Calcular una puntuacion ponderada de 0 a 100
delanteros["Puntuacion"] = 0

for columna, peso in indicadores.items():
    percentil = delanteros[f"{columna}_percentil"].fillna(0)
    delanteros["Puntuacion"] += percentil * peso * 100

# 6. Ordenar por la nueva puntuacion
ranking = delanteros.sort_values(
    by="Puntuacion",
    ascending=False
)

columnas = [
    "Player",
    "Squad",
    "Pos",
    "Min",
    "Gls",
    "Ast",
    "Gls_90",
    "Ast_90",
    "SoT_90",
    "Precision_tiro",
    "Puntuacion",
]

print(f"Candidatos analizados: {len(ranking)}")
print("\nTop 15 por puntuacion combinada:")
print(
    ranking[columnas]
    .head(15)
    .round(3)
    .to_string(index=False)
)

ranking[columnas].to_csv(
    "ranking_delanteros.csv",
    index=False
)

print("\nArchivo actualizado: ranking_delanteros.csv")
