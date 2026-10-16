
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"


def generar_informe_scouting(jugador: dict) -> str:
    """Genera un informe basado en las estadisticas disponibles."""

    if not API_KEY:
        raise RuntimeError(
            "No se encuentra GEMINI_API_KEY en el archivo .env"
        )

    client = genai.Client(api_key=API_KEY)


    prompt = f"""
    Actua como analista profesional de scouting futbolistico.

    Analiza al jugador utilizando exclusivamente los datos
    proporcionados. No inventes datos ni afirmes haber visto
    partidos, videos o mapas de calor.

    Datos del jugador:
    {jugador}

    Escribe el informe en español con estos apartados:

    1. Resumen del perfil.
    2. Fortalezas respaldadas por datos concretos.
    3. Aspectos que conviene investigar.
    4. Limitaciones del analisis.
    5. Conclusion.

    Reglas obligatorias:
    - Diferencia los hechos de las interpretaciones.
    - Cita las cifras que respaldan cada fortaleza.
    - No califiques una estadistica como buena o mala
      sin una comparacion o referencia disponible.
    - No infieras cualidades tacticas, fisicas o tecnicas
      que no puedan deducirse de los datos.
    - Considera los minutos disputados al interpretar
      las tasas por 90 minutos.
    - Si faltan datos, indica que no se puede evaluar
      ese aspecto.
    - No recomiendes fichar o descartar al jugador
      basandote unicamente en estas estadisticas.
    """

    respuesta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    if not respuesta.text:
        raise RuntimeError("El modelo no ha devuelto texto.")

    return respuesta.text
