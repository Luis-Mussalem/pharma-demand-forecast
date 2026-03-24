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
    save_governance_summary,
    save_governance_alerts,
    save_governance_panel_snapshot,
    save_promotion_report,
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
            new_metrics={"MAE": 39.5},
            current_metrics={"MAE": 40.0},
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
            "reason_code": "REJECTED_ABSOLUTE_AND_RELATIVE",
            "champion_before": "model_20260316_161656.pkl",
            "champion_after": "model_20260316_161656.pkl",
            "metric": "MAE",
            "direction": "lower",
            "challenger_metric_value": 509.0,
            "champion_metric_value": 508.0,
            "absolute_improvement": -1.0,
            "relative_improvement": -0.0019685039,
            "min_absolute_improvement": 1.0,
            "min_relative_improvement": 0.01,
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

        self.assertEqual(
            benchmark.loc[0, "promotion_reason_code"],
            "REJECTED_ABSOLUTE_AND_RELATIVE",
        )
        self.assertEqual(benchmark.loc[0, "promotion_direction"], "lower")
        self.assertEqual(benchmark.loc[0, "absolute_improvement"], -1.0)
        self.assertAlmostEqual(
            benchmark.loc[0, "relative_improvement"],
            -0.0019685039,
            places=9,
        )
        self.assertEqual(benchmark.loc[0, "min_absolute_improvement"], 1.0)
        self.assertEqual(benchmark.loc[0, "min_relative_improvement"], 0.01)

class TestPromotionReport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_generates_report_from_benchmark_history(self):
        benchmark_path = self.repo_root / "artifacts" / "benchmark_history.csv"

        pd.DataFrame(
            [
                {
                    "timestamp": "20260318_100000",
                    "promoted_to_champion": True,
                    "promotion_reason_code": "PROMOTED_THRESHOLD_MET",
                    "promotion_metric": "MAE",
                    "promotion_direction": "lower",
                    "challenger_metric_value": 503.0,
                    "champion_metric_value": 510.0,
                    "absolute_improvement": 7.0,
                    "relative_improvement": 0.01372549,
                    "min_absolute_improvement": 1.0,
                    "min_relative_improvement": 0.01,
                    "champion_before": "model_20260317_090000.pkl",
                    "champion_after": "model_20260318_100000.pkl",
                },
                {
                    "timestamp": "20260318_110000",
                    "promoted_to_champion": False,
                    "promotion_reason_code": "REJECTED_RELATIVE_THRESHOLD",
                    "promotion_metric": "MAE",
                    "promotion_direction": "lower",
                    "challenger_metric_value": 509.0,
                    "champion_metric_value": 508.0,
                    "absolute_improvement": -1.0,
                    "relative_improvement": -0.0019685,
                    "min_absolute_improvement": 1.0,
                    "min_relative_improvement": 0.01,
                    "champion_before": "model_20260318_100000.pkl",
                    "champion_after": "model_20260318_100000.pkl",
                },
            ]
        ).to_csv(benchmark_path, index=False)

        save_promotion_report(
            artifacts_dir=self.repo_root / "artifacts",
            window=50,
        )

        report_path = self.repo_root / "artifacts" / "promotion_report_latest.json"
        self.assertTrue(report_path.exists())

        with open(report_path, "r") as f:
            payload = json.load(f)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["total_runs"], 2)
        self.assertEqual(payload["audited_runs"], 2)
        self.assertAlmostEqual(payload["promotion_rate"], 0.5, places=6)
        self.assertEqual(
            payload["reason_code_distribution"]["PROMOTED_THRESHOLD_MET"],
            1,
        )
        self.assertEqual(
            payload["reason_code_distribution"]["REJECTED_RELATIVE_THRESHOLD"],
            1,
        )
        self.assertEqual(
            payload["latest_decision"]["reason_code"],
            "REJECTED_RELATIVE_THRESHOLD",
        )

    def test_generates_missing_history_report(self):
        save_promotion_report(
            artifacts_dir=self.repo_root / "artifacts",
            window=50,
        )

        report_path = self.repo_root / "artifacts" / "promotion_report_latest.json"
        self.assertTrue(report_path.exists())

        with open(report_path, "r") as f:
            payload = json.load(f)

        self.assertEqual(payload["status"], "benchmark_history_missing")
        self.assertEqual(payload["total_runs"], 0)
        self.assertEqual(payload["audited_runs"], 0)

    def test_generates_empty_history_report(self):
        benchmark_path = self.repo_root / "artifacts" / "benchmark_history.csv"
        pd.DataFrame().to_csv(benchmark_path, index=False)

        save_promotion_report(
            artifacts_dir=self.repo_root / "artifacts",
            window=50,
        )

        report_path = self.repo_root / "artifacts" / "promotion_report_latest.json"
        self.assertTrue(report_path.exists())

        with open(report_path, "r") as f:
            payload = json.load(f)

        self.assertEqual(payload["status"], "benchmark_history_empty")
        self.assertEqual(payload["total_runs"], 0)
        self.assertEqual(payload["audited_runs"], 0)

    def test_generates_missing_audit_columns_report(self):
        benchmark_path = self.repo_root / "artifacts" / "benchmark_history.csv"
        pd.DataFrame(
            [
                {
                    "timestamp": "20260318_120000",
                    "MAE": 508.0,
                    "RMSE": 779.0,
                }
            ]
        ).to_csv(benchmark_path, index=False)

        save_promotion_report(
            artifacts_dir=self.repo_root / "artifacts",
            window=50,
        )

        report_path = self.repo_root / "artifacts" / "promotion_report_latest.json"
        self.assertTrue(report_path.exists())

        with open(report_path, "r") as f:
            payload = json.load(f)

        self.assertEqual(payload["status"], "missing_audit_columns")
        self.assertEqual(payload["total_runs"], 1)
        self.assertEqual(payload["audited_runs"], 0)
        self.assertIn("promotion_reason_code", payload["missing_columns"])

class TestGovernanceSummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "config").mkdir(parents=True, exist_ok=True)

        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_generates_unified_governance_summary(self):
        (self.repo_root / "config" / "model_registry.yaml").write_text(
            "champion_model: model_20260316_161656.pkl\n"
        )

        (self.repo_root / "artifacts" / "metrics_20260316_161656.json").write_text(
            json.dumps({"MAE": 508.36, "RMSE": 779.23})
        )

        (self.repo_root / "artifacts" / "promotion_report_latest.json").write_text(
            json.dumps(
                {
                    "status": "ok",
                    "latest_decision": {
                        "timestamp": "20260319_183955",
                        "champion_after": "model_20260316_161656.pkl",
                        "reason_code": "REJECTED_ABSOLUTE_AND_RELATIVE",
                    },
                }
            )
        )

        (self.repo_root / "artifacts" / "drift_report_latest.json").write_text(
            json.dumps(
                {
                    "status": "baseline_missing",
                    "drift_detected": None,
                    "model_filename": "model_20260316_161656.pkl",
                    "drifted_features": [],
                }
            )
        )

        pd.DataFrame(
            [
                {
                    "timestamp": "20260319_183955",
                    "model": "hist_gradient_boosting",
                    "features_used": "calendar|lag|rolling|promo",
                    "MAE": 508.3677641169985,
                    "RMSE": 779.234027877473,
                }
            ]
        ).to_csv(self.repo_root / "artifacts" / "benchmark_history.csv", index=False)

        save_governance_summary(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_summary_latest.json"
        self.assertTrue(output_path.exists())

        payload = json.loads(output_path.read_text())

        self.assertEqual(
            payload["champion"]["model_filename"],
            "model_20260316_161656.pkl",
        )
        self.assertEqual(payload["champion"]["metrics"]["MAE"], 508.36)
        self.assertEqual(payload["promotion"]["report_status"], "ok")
        self.assertEqual(payload["promotion"]["latest_decision"]["reason_code"], "REJECTED_ABSOLUTE_AND_RELATIVE")
        self.assertEqual(payload["drift"]["report_status"], "baseline_missing")
        self.assertEqual(payload["latest_benchmark"]["model"], "hist_gradient_boosting")
        self.assertTrue(payload["consistency_checks"]["promotion_aligned_to_registry"])
        self.assertTrue(payload["consistency_checks"]["drift_aligned_to_registry"])

    def test_handles_missing_reports_without_crashing(self):
        (self.repo_root / "config" / "model_registry.yaml").write_text(
            "champion_model: model_20260316_161656.pkl\n"
        )

        save_governance_summary(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_summary_latest.json"
        self.assertTrue(output_path.exists())

        payload = json.loads(output_path.read_text())

        self.assertEqual(
            payload["champion"]["model_filename"],
            "model_20260316_161656.pkl",
        )
        self.assertEqual(payload["promotion"]["report_status"], "promotion_report_missing")
        self.assertEqual(payload["drift"]["report_status"], "drift_report_missing")
        self.assertIsNone(payload["latest_benchmark"])
        self.assertIsNone(payload["consistency_checks"]["promotion_aligned_to_registry"])
        self.assertIsNone(payload["consistency_checks"]["drift_aligned_to_registry"])

class TestGovernanceAlerts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_warns_when_drift_baseline_is_missing(self):
        summary = {
            "promotion": {
                "report_status": "ok",
                "latest_decision": {
                    "champion_after": "model_20260316_161656.pkl",
                },
            },
            "drift": {
                "report_status": "baseline_missing",
                "drift_detected": None,
                "model_filename": "model_20260316_161656.pkl",
                "drifted_features": [],
            },
            "consistency_checks": {
                "promotion_aligned_to_registry": True,
                "drift_aligned_to_registry": True,
            },
        }

        (self.repo_root / "artifacts" / "governance_summary_latest.json").write_text(
            json.dumps(summary)
        )

        save_governance_alerts(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_alerts_latest.json"
        payload = json.loads(output_path.read_text())

        codes = {alert["code"] for alert in payload["alerts"]}
        self.assertIn("DRIFT_BASELINE_MISSING", codes)
        self.assertEqual(payload["warn_alerts"], 1)

    def test_flags_critical_mismatch_when_registry_alignment_fails(self):
        summary = {
            "promotion": {
                "report_status": "ok",
                "latest_decision": {
                    "champion_after": "model_old.pkl",
                },
            },
            "drift": {
                "report_status": "ok",
                "drift_detected": False,
                "model_filename": "model_other.pkl",
                "drifted_features": [],
            },
            "consistency_checks": {
                "promotion_aligned_to_registry": False,
                "drift_aligned_to_registry": False,
            },
        }

        (self.repo_root / "artifacts" / "governance_summary_latest.json").write_text(
            json.dumps(summary)
        )

        save_governance_alerts(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_alerts_latest.json"
        payload = json.loads(output_path.read_text())

        codes = {alert["code"] for alert in payload["alerts"]}
        self.assertIn("PROMOTION_REGISTRY_MISMATCH", codes)
        self.assertIn("DRIFT_REGISTRY_MISMATCH", codes)
        self.assertEqual(payload["critical_alerts"], 2)

    def test_keeps_alerts_empty_for_healthy_summary(self):
        summary = {
            "promotion": {
                "report_status": "ok",
                "latest_decision": {
                    "champion_after": "model_20260316_161656.pkl",
                },
            },
            "drift": {
                "report_status": "ok",
                "drift_detected": False,
                "model_filename": "model_20260316_161656.pkl",
                "drifted_features": [],
            },
            "consistency_checks": {
                "promotion_aligned_to_registry": True,
                "drift_aligned_to_registry": True,
            },
        }

        (self.repo_root / "artifacts" / "governance_summary_latest.json").write_text(
            json.dumps(summary)
        )

        save_governance_alerts(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_alerts_latest.json"
        payload = json.loads(output_path.read_text())

        self.assertEqual(payload["total_alerts"], 0)
        self.assertEqual(payload["critical_alerts"], 0)
        self.assertEqual(payload["warn_alerts"], 0)

def test_triggers_consecutive_rejection_alert_with_custom_threshold(self):
    summary = {
        "promotion": {
            "report_status": "ok",
            "latest_decision": {
                "champion_after": "model_20260316_161656.pkl",
            },
        },
        "drift": {
            "report_status": "ok",
            "drift_detected": False,
            "model_filename": "model_20260316_161656.pkl",
            "drifted_features": [],
        },
        "consistency_checks": {
            "promotion_aligned_to_registry": True,
            "drift_aligned_to_registry": True,
        },
    }

    (self.repo_root / "artifacts" / "governance_summary_latest.json").write_text(
        json.dumps(summary)
    )

    pd.DataFrame(
        [
            {"promotion_reason_code": "REJECTED_RELATIVE_THRESHOLD"},
            {"promotion_reason_code": "REJECTED_ABSOLUTE_THRESHOLD"},
        ]
    ).to_csv(self.repo_root / "artifacts" / "benchmark_history.csv", index=False)

    save_governance_alerts(
        self.repo_root / "artifacts",
        consecutive_rejection_threshold=2,
        critical_drift_feature_threshold=5,
    )

    output_path = self.repo_root / "artifacts" / "governance_alerts_latest.json"
    payload = json.loads(output_path.read_text())

    codes = {alert["code"] for alert in payload["alerts"]}
    self.assertIn("CONSECUTIVE_PROMOTION_REJECTIONS", codes)
    self.assertEqual(payload["warn_alerts"], 1)

class TestGovernancePanelSnapshot(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_generates_dashboard_friendly_snapshot(self):
        summary = {
            "champion": {
                "model_filename": "model_20260319_183955.pkl",
                "metrics": {"MAE": 508.36, "RMSE": 779.23},
            },
            "promotion": {
                "report_status": "ok",
                "latest_decision": {
                    "reason_code": "REJECTED_ABSOLUTE_AND_RELATIVE",
                    "champion_after": "model_20260319_183955.pkl",
                },
            },
            "drift": {
                "report_status": "ok",
                "drift_detected": False,
                "drifted_features": [],
            },
            "consistency_checks": {
                "promotion_aligned_to_registry": True,
                "drift_aligned_to_registry": True,
            },
        }

        alerts = {
            "total_alerts": 1,
            "critical_alerts": 0,
            "warn_alerts": 1,
            "info_alerts": 0,
        }

        (self.repo_root / "artifacts" / "governance_summary_latest.json").write_text(
            json.dumps(summary)
        )
        (self.repo_root / "artifacts" / "governance_alerts_latest.json").write_text(
            json.dumps(alerts)
        )

        save_governance_panel_snapshot(self.repo_root / "artifacts")

        output_path = self.repo_root / "artifacts" / "governance_panel_latest.json"
        self.assertTrue(output_path.exists())

        payload = json.loads(output_path.read_text())

        self.assertEqual(payload["champion_model"], "model_20260319_183955.pkl")
        self.assertEqual(payload["promotion_status"], "ok")
        self.assertEqual(payload["alerts_total"], 1)
        self.assertEqual(payload["alerts_warn"], 1)
        self.assertEqual(payload["alerts_critical"], 0)
        self.assertEqual(payload["alerts_info"], 0)

if __name__ == "__main__":
    unittest.main()