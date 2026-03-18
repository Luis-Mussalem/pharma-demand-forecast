import json
import os
import tempfile
import unittest
import pandas as pd
from pathlib import Path

from src.artifacts import (
    archive_previous_artifacts,
    evaluate_promotion,
    load_champion_metrics,
    save_experiment_summary,
    should_promote,
    update_benchmark_history,
)


class TestPromotionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "metric": "MAE",
            "direction": "lower",
            "min_relative_improvement": 0.01,
            "min_absolute_improvement": 1.0,
        }

    def test_promote_when_no_current_metrics(self):
        new_metrics = {"MAE": 500.0, "RMSE": 780.0}

        decision = should_promote(
            new_metrics=new_metrics,
            current_metrics=None,
            policy=self.policy,
        )

        self.assertTrue(decision)

    def test_promote_when_thresholds_are_met(self):
        current_metrics = {"MAE": 510.0}
        new_metrics = {"MAE": 503.0}  # abs=7.0, rel=1.37%

        decision = should_promote(
            new_metrics=new_metrics,
            current_metrics=current_metrics,
            policy=self.policy,
        )

        self.assertTrue(decision)

    def test_do_not_promote_when_absolute_threshold_not_met(self):
        current_metrics = {"MAE": 510.0}
        new_metrics = {"MAE": 509.5}  # abs=0.5 < 1.0

        decision = should_promote(
            new_metrics=new_metrics,
            current_metrics=current_metrics,
            policy=self.policy,
        )

        self.assertFalse(decision)

    def test_do_not_promote_when_relative_threshold_not_met(self):
        current_metrics = {"MAE": 10000.0}
        new_metrics = {"MAE": 9990.0}  # abs=10.0 ok, rel=0.1% < 1%

        decision = should_promote(
            new_metrics=new_metrics,
            current_metrics=current_metrics,
            policy=self.policy,
        )

        self.assertFalse(decision)

    def test_raise_on_invalid_direction(self):
        current_metrics = {"MAE": 510.0}
        new_metrics = {"MAE": 503.0}
        invalid_policy = {
            "metric": "MAE",
            "direction": "sideways",
            "min_relative_improvement": 0.01,
            "min_absolute_improvement": 1.0,
        }

        with self.assertRaises(ValueError):
            should_promote(
                new_metrics=new_metrics,
                current_metrics=current_metrics,
                policy=invalid_policy,
            )

class TestPromotionDecisionExplainability(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "metric": "MAE",
            "direction": "lower",
            "min_relative_improvement": 0.01,
            "min_absolute_improvement": 1.0,
        }

    def test_reason_no_champion_baseline(self):
        decision = evaluate_promotion(
            new_metrics={"MAE": 500.0},
            current_metrics=None,
            policy=self.policy,
        )

        self.assertTrue(decision["promoted"])
        self.assertEqual(decision["reason_code"], "NO_CHAMPION_BASELINE")

    def test_reason_rejected_absolute_threshold(self):
        decision = evaluate_promotion(
            new_metrics={"MAE": 509.5},
            current_metrics={"MAE": 510.0},
            policy=self.policy,
        )

        self.assertFalse(decision["promoted"])
        self.assertEqual(decision["reason_code"], "REJECTED_ABSOLUTE_THRESHOLD")

    def test_reason_rejected_relative_threshold(self):
        decision = evaluate_promotion(
            new_metrics={"MAE": 9990.0},
            current_metrics={"MAE": 10000.0},
            policy=self.policy,
        )

        self.assertFalse(decision["promoted"])
        self.assertEqual(decision["reason_code"], "REJECTED_RELATIVE_THRESHOLD")

    def test_reason_promoted_threshold_met(self):
        decision = evaluate_promotion(
            new_metrics={"MAE": 503.0},
            current_metrics={"MAE": 510.0},
            policy=self.policy,
        )

        self.assertTrue(decision["promoted"])
        self.assertEqual(decision["reason_code"], "PROMOTED_THRESHOLD_MET")

class TestArchivePreviousArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_keeps_champion_model_and_metrics_in_active_artifacts(self):
        champion_model = "model_20260317_100000.pkl"
        champion_metrics = "metrics_20260317_100000.json"

        (self.repo_root / "artifacts" / champion_model).write_text("champion")
        (self.repo_root / "artifacts" / champion_metrics).write_text("{}")

        (self.repo_root / "artifacts" / "model_20260316_090000.pkl").write_text("old")
        (self.repo_root / "artifacts" / "metrics_20260316_090000.json").write_text("{}")
        (self.repo_root / "artifacts" / "benchmark_history.csv").write_text("header\n")

        archive_previous_artifacts(skip_model=champion_model)

        self.assertTrue((self.repo_root / "artifacts" / champion_model).exists())
        self.assertTrue((self.repo_root / "artifacts" / champion_metrics).exists())

        self.assertTrue(
            (self.repo_root / "archive" / "models" / "model_20260316_090000.pkl").exists()
        )
        self.assertTrue(
            (self.repo_root / "archive" / "metrics" / "metrics_20260316_090000.json").exists()
        )
        self.assertTrue((self.repo_root / "artifacts" / "benchmark_history.csv").exists())

class TestLoadChampionMetrics(unittest.TestCase):
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

    def test_returns_none_when_no_champion_registered(self):
        result = load_champion_metrics({})
        self.assertIsNone(result)

    def test_returns_none_when_champion_is_latest(self):
        result = load_champion_metrics({"champion_model": "latest"})
        self.assertIsNone(result)

    def test_returns_none_when_metrics_file_missing(self):
        result = load_champion_metrics(
            {"champion_model": "model_20260317_100000.pkl"}
        )
        self.assertIsNone(result)

    def test_returns_metrics_from_artifacts_when_file_exists(self):
        metrics_path = self.repo_root / "artifacts" / "metrics_20260317_100000.json"
        metrics_path.write_text(json.dumps({"MAE": 508.0, "RMSE": 779.0}))

        result = load_champion_metrics(
            {"champion_model": "model_20260317_100000.pkl"}
        )

        self.assertEqual(result["MAE"], 508.0)
        self.assertEqual(result["RMSE"], 779.0)

    def test_returns_metrics_from_archive_when_active_file_is_missing(self):
        archived_metrics_path = (
            self.repo_root / "archive" / "metrics" / "metrics_20260317_100000.json"
        )
        archived_metrics_path.write_text(json.dumps({"MAE": 507.5, "RMSE": 778.1}))

        result = load_champion_metrics(
            {"champion_model": "model_20260317_100000.pkl"}
        )

        self.assertEqual(result["MAE"], 507.5)
        self.assertEqual(result["RMSE"], 778.1)

class TestPromotionAuditArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_experiment_summary_includes_promotion_audit(self):
        promotion_audit = {
            "promoted": True,
            "champion_before": "model_20260316_161656.pkl",
            "champion_after": "model_20260317_101500.pkl",
            "metric": "MAE",
            "challenger_metric_value": 503.0,
            "champion_metric_value": 508.0,
        }

        save_experiment_summary(
            metrics={"MAE": 503.0, "RMSE": 779.0},
            features_used=["calendar", "lag", "rolling"],
            model_name="HistGradientBoostingRegressor",
            train_rows=1000,
            validation_rows=200,
            artifacts_dir=self.repo_root / "artifacts",
            timestamp="20260317_101500",
            promotion_audit=promotion_audit,
        )

        summary_path = (
            self.repo_root / "artifacts" / "experiment_summary_20260317_101500.json"
        )

        with open(summary_path, "r") as file:
            payload = json.load(file)

        self.assertTrue(payload["promotion_audit"]["promoted"])
        self.assertEqual(
            payload["promotion_audit"]["champion_before"],
            "model_20260316_161656.pkl",
        )
        self.assertEqual(
            payload["promotion_audit"]["champion_after"],
            "model_20260317_101500.pkl",
        )

    def test_benchmark_history_includes_promotion_audit_columns(self):
        promotion_audit = {
            "promoted": False,
            "champion_before": "model_20260316_161656.pkl",
            "champion_after": "model_20260316_161656.pkl",
            "metric": "MAE",
            "challenger_metric_value": 509.0,
            "champion_metric_value": 508.0,
        }

        update_benchmark_history(
            metrics={"MAE": 509.0, "RMSE": 781.0},
            features_used=["calendar", "lag"],
            model_name="HistGradientBoostingRegressor",
            train_rows=1000,
            validation_rows=200,
            artifacts_dir=self.repo_root / "artifacts",
            timestamp="20260317_102000",
            promotion_audit=promotion_audit,
        )

        benchmark_path = self.repo_root / "artifacts" / "benchmark_history.csv"
        benchmark = pd.read_csv(benchmark_path)

        self.assertEqual(benchmark.loc[0, "promoted_to_champion"], False)
        self.assertEqual(
            benchmark.loc[0, "champion_before"],
            "model_20260316_161656.pkl",
        )
        self.assertEqual(
            benchmark.loc[0, "champion_after"],
            "model_20260316_161656.pkl",
        )
        self.assertEqual(benchmark.loc[0, "promotion_metric"], "MAE")
        self.assertEqual(benchmark.loc[0, "challenger_metric_value"], 509.0)
        self.assertEqual(benchmark.loc[0, "champion_metric_value"], 508.0)

if __name__ == "__main__":
    unittest.main()