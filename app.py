
from scouting_ai import (
    ScoutingAPIError,
    ScoutingAuthenticationError,
    ScoutingConnectionError,
    ScoutingQuotaError,
    ScoutingResponseError,
    ScoutingServiceUnavailableError,
    generate_scouting_report,
    prepare_player_data,
)
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Football Scout AI",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Football Scout AI")
st.caption("Explora y compara candidatos a partir de sus estadísticas.")


def show_scouting_error(message: str, error: ScoutingAPIError) -> None:
    st.error(message)
    with st.expander("Detalles técnicos"):
        st.code(error.technical_detail)

df = pd.read_csv("players_clean.csv")

# Sidebar scouting filters
st.sidebar.header("Filtros de scouting")

profile = st.sidebar.selectbox(
    "Perfil de jugador",
    ["Delantero", "Centrocampista", "Defensa"],
)

minimum_minutes = st.sidebar.slider(
    "Minutos mínimos",
    min_value=0,
    max_value=3000,
    value=900,
    step=100,
)

positions = {
    "Delantero": "FW",
    "Centrocampista": "MF",
    "Defensa": "DF",
}

target_position = positions[profile]

# Include mixed positions such as MF,FW
position_mask = df["Pos"].fillna("").str.split(",").apply(
    lambda player_positions: target_position in player_positions
)

shortlist = df[
    position_mask & (df["Min"] >= minimum_minutes)
].copy()

# Initial sort by the profile's main indicator
sort_indicators = {
    "Delantero": "Gls_90",
    "Centrocampista": "Ast_90",
    "Defensa": "Int",
}

sort_indicator = sort_indicators[profile]

if sort_indicator in shortlist.columns:
    shortlist = shortlist.sort_values(
        sort_indicator,
        ascending=False,
        na_position="last",
    )

# Resumen superior
col1, col2, col3 = st.columns(3)

col1.metric("Candidatos", len(shortlist))
col2.metric("Perfil", profile)
col3.metric("Minutos mínimos", minimum_minutes)

st.subheader("Candidatos encontrados")

visible_columns = [
    c for c in [
        "Player", "Squad", "Comp", "Pos", "Age",
        "Min", "Gls", "Ast", "Gls_90", "Ast_90",
        "Sh", "SoT", "Int", "TklW"
    ]
    if c in shortlist.columns
]

st.dataframe(
    shortlist[visible_columns],
    use_container_width=True,
    hide_index=True,
)

if not shortlist.empty:
    st.subheader("Ficha del jugador")

    selected_player = st.selectbox(
        "Selecciona un jugador",
        shortlist.index,
        format_func=lambda i: (
            f"{shortlist.loc[i, 'Player']} — "
            f"{shortlist.loc[i, 'Squad']}"
        ),
    )

    player_data = shortlist.loc[selected_player]

    st.write(
        f"**{player_data['Player']}** · "
        f"{player_data['Squad']} · "
        f"{player_data['Pos']}"
    )

    metrics = st.columns(4)

    for column, column_name in zip(
        metrics,
        ["Min", "Gls", "Ast", "Gls_90"],
    ):
        if column_name in player_data.index:
            value = player_data[column_name]
            column.metric(column_name, round(value, 3) if pd.notna(value) else "N/D")

    st.divider()
    st.subheader("Informe de scouting con IA")

    if st.button("Generar informe de scouting", type="primary"):
        player_payload = prepare_player_data(player_data)

        with st.spinner("Generando informe de scouting..."):
            try:
                report = generate_scouting_report(player_payload)
                st.markdown(report)
            except ScoutingAuthenticationError as error:
                show_scouting_error(
                    "No se ha podido autenticar con el servicio de IA. "
                    "Comprueba la configuración de la API.",
                    error,
                )
            except ScoutingQuotaError as error:
                show_scouting_error(
                    "Se ha alcanzado el límite de uso del servicio de IA. "
                    "Inténtalo más tarde.",
                    error,
                )
            except ScoutingServiceUnavailableError as error:
                show_scouting_error(
                    "El servicio de IA no está disponible en este momento. "
                    "Vuelve a intentarlo en unos minutos.",
                    error,
                )
            except ScoutingConnectionError as error:
                show_scouting_error(
                    "No se ha podido conectar con el servicio de IA. "
                    "Comprueba tu conexión e inténtalo de nuevo.",
                    error,
                )
            except ScoutingResponseError as error:
                show_scouting_error(
                    "La IA no ha generado un informe válido. "
                    "Puedes volver a intentarlo.",
                    error,
                )
            except ScoutingAPIError as error:
                show_scouting_error(
                    "Ha ocurrido un error al generar el informe. "
                    "Inténtalo de nuevo.",
                    error,
                )

else:
    st.info("No hay candidatos con esos filtros.")
