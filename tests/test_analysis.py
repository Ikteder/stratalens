from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stratalens.analysis import analyze_rows
from stratalens.io import InputError, load_rows
from stratalens.report import render_html


def rows_for(stratum: str, treatment: int, outcomes: list[int], weight: float = 1.0):
    return [
        {"stratum": stratum, "treatment": treatment, "outcome": outcome, "weight": weight}
        for outcome in outcomes
    ]


class AnalysisTests(unittest.TestCase):
    def strong_fixture(self):
        rows = []
        rows += rows_for("low", 0, [1] * 1 + [0] * 9)
        rows += rows_for("low", 1, [1] * 9 + [0] * 51)
        rows += rows_for("high", 0, [1] * 36 + [0] * 24)
        rows += rows_for("high", 1, [1] * 13 + [0] * 7)
        return rows

    def test_detects_strong_reversal(self):
        result = analyze_rows(self.strong_fixture(), bootstrap=0)
        self.assertLess(result["aggregate"]["effect"], 0)
        self.assertGreater(result["standardized"]["effect"], 0)
        self.assertEqual(result["classification"]["label"], "strong_reversal")

    def test_standardization_uses_pooled_comparable_shares(self):
        result = analyze_rows(self.strong_fixture(), bootstrap=0)
        shares = [s["standardization_share"] for s in result["strata"] if s["comparable"]]
        self.assertAlmostEqual(sum(shares), 1.0)
        self.assertAlmostEqual(
            result["composition_gap"],
            result["aggregate"]["effect"] - result["standardized"]["effect"],
        )

    def test_weighted_rates_and_effective_sample_size(self):
        rows = [
            {"stratum": "a", "treatment": 0, "outcome": 0, "weight": 1.0},
            {"stratum": "a", "treatment": 0, "outcome": 1, "weight": 3.0},
            {"stratum": "a", "treatment": 1, "outcome": 1, "weight": 2.0},
        ]
        result = analyze_rows(rows, bootstrap=0)
        self.assertAlmostEqual(result["groups"]["control"]["rate"], 0.75)
        self.assertAlmostEqual(result["groups"]["control"]["effective_sample_size"], 1.6)

    def test_mixed_reversal_is_not_called_strong(self):
        rows = self.strong_fixture() + rows_for("middle", 0, [0, 0, 1, 1]) + rows_for("middle", 1, [0, 0, 0, 1])
        result = analyze_rows(rows, bootstrap=0)
        self.assertLess(result["aggregate"]["effect"], 0)
        self.assertGreater(result["standardized"]["effect"], 0)
        self.assertEqual(result["classification"]["label"], "mixed_reversal")

    def test_nonoverlap_is_reported_and_excluded(self):
        rows = self.strong_fixture() + rows_for("treated_only", 1, [1, 0, 1])
        result = analyze_rows(rows, bootstrap=0)
        missing = next(s for s in result["strata"] if s["name"] == "treated_only")
        self.assertFalse(missing["comparable"])
        self.assertLess(result["diagnostics"]["comparable_weight_share"], 1.0)

    def test_bootstrap_is_deterministic(self):
        first = analyze_rows(self.strong_fixture(), seed=17, bootstrap=60)["bootstrap"]
        second = analyze_rows(self.strong_fixture(), seed=17, bootstrap=60)["bootstrap"]
        self.assertEqual(first, second)
        self.assertEqual(first["valid"], 60)

    def test_requires_two_groups(self):
        with self.assertRaisesRegex(ValueError, "each treatment group"):
            analyze_rows(rows_for("a", 1, [0, 1]), bootstrap=0)

    def test_html_escapes_embedded_payload(self):
        result = analyze_rows(self.strong_fixture(), bootstrap=0)
        result["strata"][0]["name"] = "</script><script>alert(1)</script>"
        output = render_html(result)
        self.assertNotIn("</script><script>alert(1)</script>", output)
        self.assertIn("\\u003c/script\\u003e", output)


class InputTests(unittest.TestCase):
    def write(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "input.csv"
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_default_weight(self):
        rows = load_rows(self.write("stratum,treatment,outcome\na,0,1\na,1,0\n"))
        self.assertEqual(rows[0]["weight"], 1.0)

    def test_rejects_nonbinary_outcome(self):
        with self.assertRaises(InputError):
            load_rows(self.write("stratum,treatment,outcome\na,0,yes\n"))

    def test_rejects_invalid_weight(self):
        with self.assertRaises(InputError):
            load_rows(self.write("stratum,treatment,outcome,weight\na,0,1,-1\n"))


if __name__ == "__main__":
    unittest.main()
