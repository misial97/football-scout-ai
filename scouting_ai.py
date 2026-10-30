
import json
import math
import os
from collections.abc import Mapping
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
MIN_REPORT_LENGTH = 80

PLAYER_DATA_FIELDS = (
    "player",
    "club",
    "position",
    "age",
    "minutes",
    "goals",
    "assists",
    "goals_per_90",
    "assists_per_90",
    "shots",
    "shots_on_target",
    "shot_accuracy_pct",
)


class ScoutingAPIError(Exception):
    """Base exception for controlled Gemini/API failures."""

    def __init__(self, message: str, technical_detail: str = ""):
        super().__init__(message)
        self.technical_detail = technical_detail or message


class ScoutingAuthenticationError(ScoutingAPIError):
    """Raised when Gemini authentication or permissions fail."""


class ScoutingQuotaError(ScoutingAPIError):
    """Raised when the Gemini quota or request limit is exceeded."""


class ScoutingServiceUnavailableError(ScoutingAPIError):
    """Raised when Gemini is temporarily unavailable."""


class ScoutingConnectionError(ScoutingAPIError):
    """Raised when the request cannot reach or complete with Gemini."""


class ScoutingResponseError(ScoutingAPIError):
    """Raised when Gemini returns no usable report text."""


class ScoutingUnexpectedError(ScoutingAPIError):
    """Raised for an error that cannot be classified safely."""


def _is_missing(value: Any) -> bool:
    """Return True for null or invalid numeric values."""

    if value is None:
        return True

    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def calculate_shot_accuracy(
    shots: Any,
    shots_on_target: Any,
) -> Optional[float]:
    """Calculate shots on target as a percentage of total shots.

    Return None when data is missing, shots are zero, or the result is invalid.
    """

    if _is_missing(shots) or _is_missing(shots_on_target):
        return None

    try:
        shots_num = float(shots)
        shots_on_target_num = float(shots_on_target)
    except (TypeError, ValueError):
        return None

    if (
        not math.isfinite(shots_num)
        or not math.isfinite(shots_on_target_num)
        or shots_num <= 0
    ):
        return None

    return round(shots_on_target_num / shots_num * 100, 1)


def _to_int_or_none(value: Any) -> Optional[int]:
    if _is_missing(value):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return int(number) if math.isfinite(number) else None


def _to_float_or_none(value: Any, decimals: int = 3) -> Optional[float]:
    if _is_missing(value):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return round(number, decimals) if math.isfinite(number) else None


def prepare_player_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Build the deterministic data payload that will be sent to Gemini."""

    return {
        "player": None if _is_missing(data.get("Player")) else str(data["Player"]),
        "club": None if _is_missing(data.get("Squad")) else str(data["Squad"]),
        "position": None if _is_missing(data.get("Pos")) else str(data["Pos"]),
        "age": _to_int_or_none(data.get("Age")),
        "minutes": _to_int_or_none(data.get("Min")),
        "goals": _to_int_or_none(data.get("Gls")),
        "assists": _to_int_or_none(data.get("Ast")),
        "goals_per_90": _to_float_or_none(data.get("Gls_90")),
        "assists_per_90": _to_float_or_none(data.get("Ast_90")),
        "shots": _to_int_or_none(data.get("Sh")),
        "shots_on_target": _to_int_or_none(data.get("SoT")),
        "shot_accuracy_pct": calculate_shot_accuracy(
            data.get("Sh"),
            data.get("SoT"),
        ),
    }


def build_scouting_prompt(player: Mapping[str, Any]) -> str:
    """Build the Spanish scouting prompt from the exact model payload."""

    prompt_data = {
        field: None if _is_missing(player.get(field)) else player.get(field)
        for field in PLAYER_DATA_FIELDS
    }
    formatted_data = json.dumps(
        prompt_data,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )

    return f"""
Actúa como analista profesional de scouting futbolístico.

Analiza al jugador únicamente con los datos proporcionados a continuación.
El objeto contiene exactamente estos 12 campos:

- player: nombre del jugador (texto o None).
- club: club del jugador (texto o None).
- position: posición registrada en el dataset (texto o None).
- age: edad en años (entero o None).
- minutes: minutos disputados (entero o None).
- goals: goles registrados (entero o None).
- assists: asistencias registradas (entero o None).
- goals_per_90: goles por 90 minutos (decimal o None).
- assists_per_90: asistencias por 90 minutos (decimal o None).
- shots: tiros totales (entero o None).
- shots_on_target: tiros a puerta (entero o None).
- shot_accuracy_pct: precisión de tiro en porcentaje (decimal o None).

Clasifica la información del siguiente modo:

HECHOS
- Trata como hechos únicamente los valores recibidos en el objeto.
- Conserva correctamente sus valores y unidades.
- No inventes estadísticas, datos biográficos, características físicas ni
  información táctica.
- No afirmes que has visto jugar al futbolista ni que has analizado partidos,
  vídeos o mapas de calor.

CÁLCULOS
- goals_per_90 = goals / minutes * 90.
- assists_per_90 = assists / minutes * 90.
- shot_accuracy_pct = shots_on_target / shots * 100.
- Las tres métricas anteriores son cálculos deterministas realizados en Python;
  no son estadísticas originales independientes. Utilízalas tal como aparecen
  y no inventes estimaciones adicionales.
- No confundas precisión de tiro con porcentaje de conversión de gol:
  la precisión de tiro usa tiros a puerta / tiros totales; la conversión de gol
  usaría goles / tiros y no está disponible como campo calculado.
- Si faltan valores o el denominador es cero, la métrica correspondiente
  aparece como None y debes indicar que no puede calcularse o evaluarse.
- Si detectas una posible inconsistencia aritmética, señálala como limitación;
  no sustituyas silenciosamente el valor recibido.

INTERPRETACIONES
- Respalda cada conclusión con cifras concretas del objeto.
- No califiques una estadística como buena o mala sin una referencia comparativa.
- Ten en cuenta los minutos disputados y el tamaño de la muestra, especialmente
  al interpretar métricas por 90 y porcentajes.
- Distingue una fortaleza estadística de una cualidad futbolística no demostrable
  con estos datos.
- No infieras velocidad, técnica, posicionamiento, inteligencia táctica o
  capacidad defensiva si estos datos no permiten evaluarlo.
- No recomiendes fichar o descartar al jugador basándote exclusivamente en
  estas estadísticas.

Datos del jugador:
{formatted_data}

Escribe el informe en español con esta estructura exacta:

1. Resumen del perfil.
2. Datos objetivos del jugador.
3. Métricas calculadas.
4. Fortalezas respaldadas por estadísticas.
5. Aspectos que conviene investigar.
6. Limitaciones del análisis.
7. Conclusión del scouting.

En los apartados de datos objetivos y métricas calculadas, indica claramente
qué valores son None y no los interpretes como cero.
"""


def _technical_detail(error: BaseException) -> str:
    """Create a debugging detail without exposing configuration values."""

    return f"{type(error).__name__}: {error}"


def _map_api_error(error: genai_errors.APIError) -> ScoutingAPIError:
    code = getattr(error, "code", None)
    detail = _technical_detail(error)

    if code in (401, 403):
        return ScoutingAuthenticationError(
            "Gemini authentication failed.",
            detail,
        )
    if code == 429:
        return ScoutingQuotaError(
            "Gemini quota or request limit was exceeded.",
            detail,
        )
    if code in (500, 502, 503, 504):
        return ScoutingServiceUnavailableError(
            "Gemini is temporarily unavailable.",
            detail,
        )

    return ScoutingAPIError("Gemini returned an API error.", detail)


def _raise_connection_error(error: BaseException) -> None:
    raise ScoutingConnectionError(
        "The request to Gemini could not be completed.",
        _technical_detail(error),
    ) from error


def validate_scouting_response(response: Any) -> str:
    """Return usable response text or raise a controlled response error."""

    if response is None:
        raise ScoutingResponseError(
            "Gemini returned no response.",
            "The SDK response object was None.",
        )

    text = getattr(response, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise ScoutingResponseError(
            "Gemini returned empty report text.",
            "The response.text attribute was empty or not a string.",
        )

    cleaned_text = text.strip()
    if len(cleaned_text) < MIN_REPORT_LENGTH:
        raise ScoutingResponseError(
            "Gemini returned an incomplete report.",
            f"The stripped response contained {len(cleaned_text)} characters; "
            f"minimum is {MIN_REPORT_LENGTH}.",
        )

    return cleaned_text


def generate_scouting_report(player: Mapping[str, Any]) -> str:
    """Generate a report based on the available statistics."""

    if not API_KEY:
        raise ScoutingAuthenticationError(
            "Gemini API key is not configured.",
            "GEMINI_API_KEY was not found in the environment.",
        )

    prompt = build_scouting_prompt(player)

    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
    except genai_errors.APIError as error:
        mapped_error = _map_api_error(error)
        raise mapped_error from error
    except httpx.TimeoutException as error:
        _raise_connection_error(error)
    except (httpx.NetworkError, httpx.RequestError, ConnectionError) as error:
        _raise_connection_error(error)
    except Exception as error:
        raise ScoutingUnexpectedError(
            "An unexpected error occurred while contacting Gemini.",
            _technical_detail(error),
        ) from error

    try:
        return validate_scouting_response(response)
    except ScoutingResponseError:
        raise
    except Exception as error:
        raise ScoutingResponseError(
            "Gemini returned an unreadable response.",
            _technical_detail(error),
        ) from error
