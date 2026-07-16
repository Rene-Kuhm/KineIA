import unittest
from pathlib import Path

from scripts.evaluate import (
    OSCE_AXES,
    OSCEScorer,
    PreguntaBenchmark,
    RespuestaKineIA,
    calculate_osce_scores,
    parse_benchmark,
)


class CalculateOscScoresTests(unittest.TestCase):
    def test_maximum_axis_scores_map_to_the_public_ceiling(self) -> None:
        scores = {axis: 5 for axis in OSCE_AXES}

        total, categories = calculate_osce_scores(scores)

        self.assertAlmostEqual(total, 160.0)
        for score in categories.values():
            self.assertAlmostEqual(score, 100.0)

    def test_minimum_axis_scores_preserve_the_rubric_floor(self) -> None:
        scores = {axis: 1 for axis in OSCE_AXES}

        total, categories = calculate_osce_scores(scores)

        self.assertAlmostEqual(total, 32.0)
        self.assertTrue(categories)
        for score in categories.values():
            self.assertAlmostEqual(score, 20.0)

    def test_mixed_axis_scores_are_proportional_to_configured_weights(self) -> None:
        scores = {axis: 1 for axis in OSCE_AXES}
        scores["H1"] = 5

        total, categories = calculate_osce_scores(scores)

        self.assertAlmostEqual(total, 35.2)
        self.assertAlmostEqual(categories["Anamnesis"], 100.0 / 3.0)
        for category in ("Diagnóstico", "Manejo", "Comunicación", "Integración"):
            self.assertAlmostEqual(categories[category], 20.0)

    def test_missing_axis_score_is_rejected_explicitly(self) -> None:
        scores = {axis: 3 for axis in OSCE_AXES}
        del scores["H1"]

        with self.assertRaisesRegex(ValueError, "Missing OSCE axis scores: H1"):
            calculate_osce_scores(scores)

    def test_axis_scores_outside_the_one_to_five_rubric_are_rejected(self) -> None:
        for invalid_score in (0, 6):
            with self.subTest(invalid_score=invalid_score):
                scores = {axis: 3 for axis in OSCE_AXES}
                scores["H1"] = invalid_score

                with self.assertRaisesRegex(ValueError, f"H1={invalid_score}"):
                    calculate_osce_scores(scores)


class OscScorerTests(unittest.TestCase):
    def test_successful_response_does_not_automatically_saturate_total_score(self) -> None:
        question = PreguntaBenchmark(
            id="test-1",
            area="Traumatología",
            tema="Evaluación",
            dificultad="Básico",
            modo="Profesional",
            pregunta="¿Qué evaluaría?",
            respuesta_esperada="evaluación",
        )
        response = RespuestaKineIA(
            pregunta_id=question.id,
            query=question.pregunta,
            answer="",
            sources=[],
            response_time_ms=1,
            mode="professional",
        )

        result = OSCEScorer().score_answer(question, response)

        self.assertGreater(result.score_total, 0.0)
        self.assertLess(result.score_total, 160.0)


class BenchmarkParserTests(unittest.TestCase):
    def test_template_is_not_counted_as_a_completed_question(self) -> None:
        benchmark_path = Path(__file__).parents[2] / "docs" / "benchmark-preguntas.md"

        questions = parse_benchmark(str(benchmark_path))

        self.assertEqual(len(questions), 15)
        self.assertNotIn("???", {question.id for question in questions})


if __name__ == "__main__":
    unittest.main()
