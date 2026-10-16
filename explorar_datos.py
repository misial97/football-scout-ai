
import pandas as pd

# 1. Cargar el archivo CSV
df = pd.read_csv("players_data-2025_2026.csv")

# 2. Mostrar las dimensiones de la tabla
print("Filas y columnas:")
print(df.shape)

# 3. Ver los nombres de las columnas
print("\nColumnas disponibles:")
print(df.columns.tolist())

# 4. Ver los primeros cinco jugadores
print("\nPrimeros cinco jugadores:")
print(df[["Player", "Pos", "Squad", "Min", "Gls", "Ast"]].head())

# 5. Comprobar los datos que faltan
print("\nValores ausentes por columna:")
print(df.isna().sum().sort_values(ascending=False).head(10))

# 6. Resumen general
print("\nResumen estadístico:")
print(df[["Age", "Min", "Gls", "Ast"]].describe())


# 7. Cuantos jugadores hay por posicion
print("\nJugadores por posicion:")
print(df["Pos"].value_counts(dropna=False))

# 8. Comprobar jugadores duplicados
print("\nFilas completamente duplicadas:")
print(df.duplicated().sum())

print("\nNombres de jugador duplicados:")
print(df["Player"].duplicated().sum())

# 9. Porcentaje de valores ausentes por columna
print("\nColumnas con mas del 50% de datos ausentes:")
ausentes = df.isna().mean() * 100

print(
    ausentes[ausentes > 50]
    .sort_values(ascending=False)
    .round(1)
    .astype(str) + "%"
)

# 10. Comprobar minutos y goles
print("\nResumen de minutos y goles:")
print(df[["Min", "90s", "Gls", "Ast"]].describe())
