import math
from datetime import datetime

import pandas as pd

from src.logger import get_logger

logger = get_logger()


def compute_distribution_baseline(X: pd.DataFrame) -> dict:
    """
    Compute baseline distribution statistics for numeric model input features.
    """

    logger.info("Computing distribution baseline.")

    numeric_features = X.select_dtypes(include=["number"]).copy()

    feature_stats = {}

    for column in numeric_features.columns:
        series = pd.to_numeric(numeric_features[column], errors="coerce").dropna()

        if series.empty:
            continue

        feature_stats[column] = {
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "min": float(series.min()),
            "max": float(series.max()),
            "observations": int(series.shape[0]),
        }

    baseline = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "features_evaluated": int(len(feature_stats)),
        "feature_stats": feature_stats,
    }

    logger.info(
        "Distribution baseline computed successfully. Features evaluated: %s",
        baseline["features_evaluated"],
    )

    return baseline


def detect_drift(
    X: pd.DataFrame,
    baseline: dict,
    z_score_threshold: float,
) -> dict:
    """
    Detect drift by comparing current feature means against baseline means
    using baseline standard deviation as the normalization factor.
    """

    logger.info("Detecting inference drift.")

    numeric_features = X.select_dtypes(include=["number"]).copy()
    baseline_feature_stats = baseline.get("feature_stats", {})

    feature_details = {}
    drifted_features = []

    for column, stats in baseline_feature_stats.items():
        if column not in numeric_features.columns:
            feature_details[column] = {
                "status": "missing_in_current_data",
                "baseline_mean": stats["mean"],
                "baseline_std": stats["std"],
                "current_mean": None,
                "mean_shift": None,
                "z_score": None,
                "drift_detected": None,
            }
            continue

        series = pd.to_numeric(numeric_features[column], errors="coerce").dropna()

        if series.empty:
            feature_details[column] = {
                "status": "no_current_observations",
                "baseline_mean": stats["mean"],
                "baseline_std": stats["std"],
                "current_mean": None,
                "mean_shift": None,
                "z_score": None,
                "drift_detected": None,
            }
            continue

        baseline_mean = float(stats["mean"])
        baseline_std = float(stats["std"])
        current_mean = float(series.mean())
        mean_shift = abs(current_mean - baseline_mean)

        if baseline_std == 0.0:
            z_score = 0.0 if mean_shift == 0.0 else math.inf
        else:
            z_score = mean_shift / baseline_std

        drift_detected = z_score > z_score_threshold

        if drift_detected:
            drifted_features.append(column)

        feature_details[column] = {
            "status": "evaluated",
            "baseline_mean": baseline_mean,
            "baseline_std": baseline_std,
            "current_mean": current_mean,
            "mean_shift": mean_shift,
            "z_score": z_score,
            "drift_detected": drift_detected,
        }

    status = "drift_detected" if drifted_features else "ok"

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "drift_detected": bool(drifted_features),
        "z_score_threshold": float(z_score_threshold),
        "features_evaluated": int(len(feature_details)),
        "drifted_features": drifted_features,
        "feature_details": feature_details,
    }

    logger.info(
        "Inference drift detection completed. Status: %s | Drifted features: %s",
        status,
        len(drifted_features),
    )

    return report