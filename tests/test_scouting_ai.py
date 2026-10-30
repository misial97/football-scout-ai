import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scouting_ai import (
    PLAYER_DATA_FIELDS,
    ScoutingAuthenticationError,
    ScoutingConnectionError,
    ScoutingQuotaError,
    ScoutingResponseError,
    ScoutingServiceUnavailableError,
    ScoutingUnexpectedError,
    build_scouting_prompt,
    calculate_shot_accuracy,
    generate_scouting_report,
    prepare_player_data,
)
from google.genai import errors as genai_errors
import httpx


class CalculateShotAccuracyTests(unittest.TestCase):
    def test_calculates_percentage_and_rounds_to_one_decimal(self):
        self.assertEqual(calculate_shot_accuracy(47, 17), 36.2)

    def test_returns_none_when_there_are_no_shots(self):
        self.assertIsNone(calculate_shot_accuracy(0, 0))

    def test_returns_none_when_a_value_is_missing(self):
        self.assertIsNone(calculate_shot_accuracy(None, 4))
        self.assertIsNone(calculate_shot_accuracy(10, None))


class PreparePlayerDataTests(unittest.TestCase):
    def test_prepares_payload_with_expected_fields(self):
        data = {
            "Player": "Jugador Ejemplo",
            "Squad": "Club Ejemplo",
            "Pos": "FW",
            "Age": 24.0,
            "Min": 2449,
            "Gls": 4,
            "Ast": 5,
            "Gls_90": 0.146999,
            "Ast_90": 0.183748,
            "Sh": 47,
            "SoT": 17,
        }

        result = prepare_player_data(data)

        self.assertEqual(
            list(result),
            [
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
            ],
        )
        self.assertEqual(result["goals_per_90"], 0.147)
        self.assertEqual(result["shot_accuracy_pct"], 36.2)

    def test_preserves_none_for_missing_data(self):
        data = {
            "Player": "Jugador sin edad",
            "Squad": "Club Ejemplo",
            "Pos": "MF",
            "Age": None,
            "Min": 900,
            "Gls": 1,
            "Ast": 2,
            "Gls_90": 0.1,
            "Ast_90": 0.2,
            "Sh": 0,
            "SoT": 0,
        }

        result = prepare_player_data(data)

        self.assertIsNone(result["age"])
        self.assertIsNone(result["shot_accuracy_pct"])


class BuildScoutingPromptTests(unittest.TestCase):
    def test_prompt_documents_the_exact_payload_fields_and_structure(self):
        prompt = build_scouting_prompt(
            {
                "player": "Jugador Ejemplo",
                "minutes": 900,
                "age": None,
                "shot_accuracy_pct": None,
            }
        )

        self.assertEqual(len(PLAYER_DATA_FIELDS), 12)
        for field in PLAYER_DATA_FIELDS:
            self.assertIn(field, prompt)

        self.assertIn("exactamente estos 12 campos", prompt)
        self.assertIn("goals_per_90 = goals / minutes * 90", prompt)
        self.assertIn(
            "shot_accuracy_pct = shots_on_target / shots * 100",
            prompt,
        )
        self.assertIn("1. Resumen del perfil.", prompt)
        self.assertIn("7. Conclusión del scouting.", prompt)
        self.assertIn('"age": null', prompt)
        self.assertNotIn("ocho campos", prompt.lower())


class GenerateScoutingReportTests(unittest.TestCase):
    PLAYER = {"player": "Test Player"}

    def _run_with_response(self, response):
        client = Mock()
        client.models.generate_content.return_value = response
        with patch("scouting_ai.API_KEY", "configured-for-test"), patch(
            "scouting_ai.genai.Client", return_value=client
        ):
            return generate_scouting_report(self.PLAYER)

    def test_returns_valid_report_text(self):
        report = self._run_with_response(
            SimpleNamespace(text="A valid scouting report. " * 5)
        )
        self.assertTrue(report.startswith("A valid scouting report."))

    def test_rejects_none_response(self):
        with self.assertRaises(ScoutingResponseError):
            self._run_with_response(None)

    def test_rejects_empty_response(self):
        with self.assertRaises(ScoutingResponseError):
            self._run_with_response(SimpleNamespace(text="   "))

    def test_rejects_short_response(self):
        with self.assertRaises(ScoutingResponseError):
            self._run_with_response(SimpleNamespace(text="Too short"))

    def test_maps_authentication_error(self):
        error = genai_errors.ClientError(401, {"message": "unauthorized"})
        with self.assertRaises(ScoutingAuthenticationError):
            self._run_with_exception(error)

    def test_maps_quota_error(self):
        error = genai_errors.ClientError(429, {"message": "rate limited"})
        with self.assertRaises(ScoutingQuotaError):
            self._run_with_exception(error)

    def test_maps_temporary_server_error(self):
        error = genai_errors.ServerError(503, {"message": "unavailable"})
        with self.assertRaises(ScoutingServiceUnavailableError):
            self._run_with_exception(error)

    def test_maps_connection_error(self):
        error = httpx.ConnectError("connection failed")
        with self.assertRaises(ScoutingConnectionError):
            self._run_with_exception(error)

    def test_maps_unexpected_error(self):
        with self.assertRaises(ScoutingUnexpectedError):
            self._run_with_exception(ValueError("unexpected"))

    def _run_with_exception(self, error):
        client = Mock()
        client.models.generate_content.side_effect = error
        with patch("scouting_ai.API_KEY", "configured-for-test"), patch(
            "scouting_ai.genai.Client", return_value=client
        ):
            return generate_scouting_report(self.PLAYER)


if __name__ == "__main__":
    unittest.main()
