
from scouting_ai import generar_informe_scouting
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Football Scout AI",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Football Scout AI")
st.caption("Explora y compara candidatos a partir de sus estadísticas.")

df = pd.read_csv("players_clean.csv")

# Filtros de la barra lateral
st.sidebar.header("Filtros de scouting")

perfil = st.sidebar.selectbox(
    "Perfil de jugador",
    ["Delantero", "Centrocampista", "Defensa", "Portero"],
)

minutos_minimos = st.sidebar.slider(
    "Minutos mínimos",
    min_value=0,
    max_value=3000,
    value=900,
    step=100,
)

posiciones = {
    "Delantero": "FW",
    "Centrocampista": "MF",
    "Defensa": "DF",
    "Portero": "GK",
}

posicion_buscada = posiciones[perfil]

# Admitir posiciones mixtas, como MF,FW
mask_posicion = df["Pos"].fillna("").str.split(",").apply(
    lambda posiciones: posicion_buscada in posiciones
)

candidatos = df[
    mask_posicion & (df["Min"] >= minutos_minimos)
].copy()

# Orden inicial según el indicador principal del perfil
indicadores = {
    "Delantero": "Gls_90",
    "Centrocampista": "Ast_90",
    "Defensa": "Int",
    "Portero": "Save%",
}

indicador = indicadores[perfil]

if indicador in candidatos.columns:
    candidatos = candidatos.sort_values(
        indicador,
        ascending=False,
        na_position="last",
    )

# Resumen superior
col1, col2, col3 = st.columns(3)

col1.metric("Candidatos", len(candidatos))
col2.metric("Perfil", perfil)
col3.metric("Minutos mínimos", minutos_minimos)

st.subheader("Candidatos encontrados")

columnas_visibles = [
    c for c in [
        "Player", "Squad", "Comp", "Pos", "Age",
        "Min", "Gls", "Ast", "Gls_90", "Ast_90",
        "Sh", "SoT", "Int", "TklW", "Save%"
    ]
    if c in candidatos.columns
]

st.dataframe(
    candidatos[columnas_visibles],
    use_container_width=True,
    hide_index=True,
)

if not candidatos.empty:
    st.subheader("Ficha del jugador")

    jugador = st.selectbox(
        "Selecciona un jugador",
        candidatos.index,
        format_func=lambda i: (
            f"{candidatos.loc[i, 'Player']} — "
            f"{candidatos.loc[i, 'Squad']}"
        ),
    )

    datos = candidatos.loc[jugador]

    st.write(
        f"**{datos['Player']}** · "
        f"{datos['Squad']} · "
        f"{datos['Pos']}"
    )

    metricas = st.columns(4)

    for col, nombre in zip(
        metricas,
        ["Min", "Gls", "Ast", "Gls_90"],
    ):
        if nombre in datos.index:
            valor = datos[nombre]
            col.metric(nombre, round(valor, 3) if pd.notna(valor) else "N/D")

    st.divider()
    st.subheader("Informe de scouting con IA")

    if st.button("Generar informe de scouting", type="primary"):
        precision_tiro = None

        if datos["Sh"] and datos["Sh"] > 0:
            precision_tiro = datos["SoT"] / datos["Sh"] * 100

        datos_jugador = {
            "jugador": str(datos["Player"]),
            "club": str(datos["Squad"]),
            "posicion": str(datos["Pos"]),
            "edad": int(datos["Age"])
                if pd.notna(datos["Age"]) else None,
            "minutos": int(datos["Min"]),
            "goles": int(datos["Gls"]),
            "asistencias": int(datos["Ast"]),
            "goles_por_90": round(float(datos["Gls_90"]), 3),
            "asistencias_por_90": round(float(datos["Ast_90"]), 3),
            "tiros": int(datos["Sh"])
                if pd.notna(datos["Sh"]) else None,
            "tiros_a_puerta": int(datos["SoT"])
                if pd.notna(datos["SoT"]) else None,
            "precision_tiro_pct": round(precision_tiro, 1)
                if precision_tiro is not None else None,
        }

        with st.spinner("Generando informe de scouting..."):
            try:
                informe = generar_informe_scouting(datos_jugador)
                st.markdown(informe)
            except Exception as error:
                st.error(
                    "No se ha podido generar el informe. "
                    "Comprueba la conexión con la API y vuelve a intentarlo."
                )
                print(f"Error al generar informe: {error}")

else:
    st.info("No hay candidatos con esos filtros.")
