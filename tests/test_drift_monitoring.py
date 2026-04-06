import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.artifacts import (
    archive_previous_artifacts,
    load_distribution_baseline_for_model,
    save_distribution_baseline,
    save_drift_report,
)
from src.drift import compute_distribution_baseline, detect_drift


class TestDistributionBaseline(unittest.TestCase):
    def test_computes_stats_for_numeric_features_only(self):
        X = pd.DataFrame(
            {
                "Store": [1, 2, 3],
                "Promo": [0, 1, 1],
                "StateHolidayText": ["0", "a", "0"],
            }
        )

        baseline = compute_distribution_baseline(X)

        self.assertEqual(baseline["features_evaluated"], 2)
        self.assertIn("Store", baseline["feature_stats"])
        self.assertIn("Promo", baseline["feature_stats"])
        self.assertNotIn("StateHolidayText", baseline["feature_stats"])

    def test_detects_no_drift_when_shift_is_within_threshold(self):
        baseline = compute_distribution_baseline(
            pd.DataFrame({"Promo": [0.0, 1.0, 0.0, 1.0]})
        )

        report = detect_drift(
            X=pd.DataFrame({"Promo": [0.0, 1.0, 0.0, 1.1]}),
            baseline=baseline,
            z_score_threshold=3.0,
        )

        self.assertEqual(report["status"], "ok")
        self.assertFalse(report["drift_detected"])
        self.assertEqual(report["drifted_features"], [])

    def test_detects_drift_when_shift_exceeds_threshold(self):
        baseline = compute_distribution_baseline(
            pd.DataFrame({"Customers": [10.0, 11.0, 9.0, 10.0]})
        )

        report = detect_drift(
            X=pd.DataFrame({"Customers": [30.0, 31.0, 29.0, 30.0]}),
            baseline=baseline,
            z_score_threshold=3.0,
        )

        self.assertEqual(report["status"], "drift_detected")
        self.assertTrue(report["drift_detected"])
        self.assertIn("Customers", report["drifted_features"])

    def test_handles_zero_std_without_error(self):
        baseline = compute_distribution_baseline(
            pd.DataFrame({"Promo2": [1.0, 1.0, 1.0]})
        )

        report = detect_drift(
            X=pd.DataFrame({"Promo2": [2.0, 2.0, 2.0]}),
            baseline=baseline,
            z_score_threshold=3.0,
        )

        self.assertEqual(report["status"], "drift_detected")
        self.assertTrue(report["feature_details"]["Promo2"]["drift_detected"])


class TestDistributionBaselineArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "archive" / "metrics").mkdir(parents=True, exist_ok=True)

        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_loads_distribution_baseline_from_active_artifacts(self):
        baseline = {
            "generated_at": "2026-03-19T10:00:00",
            "features_evaluated": 1,
            "feature_stats": {
                "Promo": {
                    "mean": 0.5,
                    "std": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "observations": 4,
                }
            },
        }

        save_distribution_baseline(
            baseline=baseline,
            artifacts_dir=self.repo_root / "artifacts",
            timestamp="20260319_100000",
        )

        loaded = load_distribution_baseline_for_model("model_20260319_100000.pkl")

        self.assertEqual(loaded["feature_stats"]["Promo"]["mean"], 0.5)

    def test_backfills_missing_champion_baseline_from_latest_available(self):
        expected_name = "distribution_baseline_20260316_161656.json"

        source_path = (
            self.repo_root
            / "artifacts"
            / "distribution_baseline_20260406_124225.json"
        )
        source_path.write_text(
            json.dumps(
                {
                    "generated_at": "2026-04-06T12:42:15",
                    "features_evaluated": 1,
                    "feature_stats": {
                        "Promo": {
                            "mean": 0.5,
                            "std": 0.5,
                            "min": 0.0,
                            "max": 1.0,
                            "observations": 4,
                        }
                    },
                }
            )
        )

        loaded = load_distribution_baseline_for_model("model_20260316_161656.pkl")

        self.assertIsNotNone(loaded)
        self.assertTrue((self.repo_root / "artifacts" / expected_name).exists())
        self.assertEqual(loaded["generated_at"], "2026-04-06T12:42:15")

    def test_loads_distribution_baseline_from_archive_fallback(self):
        baseline_path = (
            self.repo_root
            / "archive"
            / "metrics"
            / "distribution_baseline_20260319_100000.json"
        )
        baseline_path.write_text(
            json.dumps(
                {
                    "generated_at": "2026-03-19T10:00:00",
                    "features_evaluated": 1,
                    "feature_stats": {
                        "Promo": {
                            "mean": 0.5,
                            "std": 0.5,
                            "min": 0.0,
                            "max": 1.0,
                            "observations": 4,
                        }
                    },
                }
            )
        )

        loaded = load_distribution_baseline_for_model("model_20260319_100000.pkl")

        self.assertEqual(loaded["feature_stats"]["Promo"]["max"], 1.0)

    def test_archive_preserves_champion_distribution_baseline(self):
        champion_model = "model_20260319_100000.pkl"
        champion_baseline = "distribution_baseline_20260319_100000.json"

        (self.repo_root / "artifacts" / champion_model).write_text("champion-model")
        (self.repo_root / "artifacts" / champion_baseline).write_text("{}")

        (self.repo_root / "artifacts" / "model_20260318_090000.pkl").write_text("old-model")
        (
            self.repo_root / "artifacts" / "distribution_baseline_20260318_090000.json"
        ).write_text("{}")

        archive_previous_artifacts(skip_model=champion_model)

        self.assertTrue((self.repo_root / "artifacts" / champion_baseline).exists())
        self.assertTrue(
            (
                self.repo_root
                / "archive"
                / "metrics"
                / "distribution_baseline_20260318_090000.json"
            ).exists()
        )

    def test_saves_drift_report_latest_artifact(self):
        report = {
            "generated_at": "2026-03-19T10:00:00",
            "status": "ok",
            "drift_detected": False,
            "z_score_threshold": 3.0,
            "features_evaluated": 2,
            "drifted_features": [],
            "feature_details": {},
        }

        save_drift_report(report, self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "drift_report_latest.json"

        self.assertTrue(output_path.exists())

        payload = json.loads(output_path.read_text())
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()