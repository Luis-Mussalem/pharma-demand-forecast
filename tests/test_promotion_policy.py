import unittest

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


if __name__ == "__main__":
    unittest.main()