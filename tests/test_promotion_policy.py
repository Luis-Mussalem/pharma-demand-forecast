import json
import os
import tempfile
import unittest
from pathlib import Path

from src.artifacts import should_promote


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


class TestLoadChampionMetrics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)
        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_returns_none_when_no_champion_registered(self):
        from src.artifacts import load_champion_metrics

        result = load_champion_metrics({})

        self.assertIsNone(result)

    def test_returns_none_when_champion_is_latest(self):
        from src.artifacts import load_champion_metrics

        result = load_champion_metrics({"champion_model": "latest"})

        self.assertIsNone(result)

    def test_returns_none_when_metrics_file_missing(self):
        from src.artifacts import load_champion_metrics

        result = load_champion_metrics(
            {"champion_model": "model_20260317_100000.pkl"}
        )

        self.assertIsNone(result)

    def test_returns_metrics_when_file_exists(self):
        from src.artifacts import load_champion_metrics

        metrics_path = self.repo_root / "artifacts" / "metrics_20260317_100000.json"
        metrics_path.write_text(json.dumps({"MAE": 508.0, "RMSE": 779.0}))

        result = load_champion_metrics(
            {"champion_model": "model_20260317_100000.pkl"}
        )

        self.assertEqual(result["MAE"], 508.0)
        self.assertEqual(result["RMSE"], 779.0)


if __name__ == "__main__":
    unittest.main()