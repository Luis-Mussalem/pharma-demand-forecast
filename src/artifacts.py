import json
import joblib
import pandas as pd
import shutil
import yaml

from datetime import datetime
from pathlib import Path

from src.logger import get_logger

logger = get_logger()


def generate_timestamp() -> str:
    """
    Generate timestamp for versioned artifact names.
    """

    return datetime.now().strftime("%Y%m%d_%H%M%S")

def archive_previous_artifacts(skip_model: str | None = None):
    """
    Move previous artifacts to archive folders before saving new outputs.
    Preserves champion model, champion metrics, and champion distribution baseline
    when skip_model is provided.
    """

    logger.info("Archiving previous artifacts.")

    artifacts_dir = Path("artifacts")
    archive_dir = Path("archive")

    skip_files = set()

    if skip_model and skip_model != "latest":
        skip_files.add(skip_model)

        model_stem = Path(skip_model).stem
        if model_stem.startswith("model_"):
            champion_timestamp = model_stem[len("model_"):]
            skip_files.add(f"metrics_{champion_timestamp}.json")
            skip_files.add(f"distribution_baseline_{champion_timestamp}.json")

    folder_mapping = {
        "model_": "models",
        "metrics_": "metrics",
        "distribution_baseline_": "metrics",
        "experiment_summary_": "metrics",
        "feature_importance_": "metrics",
        "predictions_": "predictions",
        "top_errors_": "diagnostics",
        "error_by_store_": "diagnostics",
    }

    for file_path in artifacts_dir.iterdir():

        if file_path.name == "benchmark_history.csv":
            continue

        if file_path.name in skip_files:
            logger.info(f"Retaining champion artifact in active folder: {file_path.name}")
            continue

        for prefix, destination in folder_mapping.items():

            if file_path.name.startswith(prefix):

                target_dir = archive_dir / destination
                target_dir.mkdir(parents=True, exist_ok=True)

                shutil.move(
                    str(file_path),
                    str(target_dir / file_path.name)
                )

                break

    logger.info("Previous artifacts archived successfully.")

def archive_inference_artifacts():
    """
    Move previous inference artifacts before saving new inference output.
    """

    logger.info("Archiving previous inference artifacts.")

    artifacts_dir = Path("artifacts")
    archive_dir = Path("archive") / "predictions"

    archive_dir.mkdir(parents=True, exist_ok=True)

    for file_path in artifacts_dir.iterdir():

        if file_path.name.startswith("inference_predictions_"):

            shutil.move(
                str(file_path),
                str(archive_dir / file_path.name)
            )

    logger.info("Previous inference artifacts archived successfully.")

def save_model(model, output_dir: Path, timestamp: str) -> None:
    """
    Save trained model artifact.
    """

    logger.info("Saving trained model artifact.")

    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / f"model_{timestamp}.pkl"

    joblib.dump(model, model_path)

    logger.info(f"Model saved at {model_path}")


def save_metrics(metrics: dict, output_dir: Path, timestamp: str) -> None:
    """
    Save evaluation metrics artifact.
    """

    logger.info("Saving evaluation metrics artifact.")

    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = output_dir / f"metrics_{timestamp}.json"

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)

    logger.info(f"Metrics saved at {metrics_path}")

def save_distribution_baseline(
    baseline: dict,
    artifacts_dir: Path,
    timestamp: str,
) -> None:
    """
    Save model-input distribution baseline aligned to a training artifact timestamp.
    """

    logger.info("Saving distribution baseline artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    output_path = artifacts_dir / f"distribution_baseline_{timestamp}.json"

    with open(output_path, "w") as file:
        json.dump(baseline, file, indent=4)

    logger.info(f"Distribution baseline saved at {output_path}")

def save_predictions(validation_df, predictions, output_dir: Path, timestamp: str) -> None:
    """
    Save validation predictions artifact.
    """

    logger.info("Saving validation predictions artifact.")

    output_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = output_dir / f"predictions_{timestamp}.csv"

    result = validation_df[["Store", "Date", "Sales"]].copy()

    result["predicted_sales"] = predictions
    result["absolute_error"] = (result["Sales"] - result["predicted_sales"]).abs()

    result = result.rename(columns={"Sales": "actual_sales"})

    result.to_csv(predictions_path, index=False)

    logger.info(f"Predictions saved at {predictions_path}")

def save_top_errors(
    validation_df: pd.DataFrame,
    predictions,
    output_dir: Path,
    timestamp: str,
    top_n: int = 20
) -> None:
    """
    Save top prediction errors for diagnostic analysis.
    """

    logger.info("Saving top prediction errors artifact.")

    output_dir.mkdir(parents=True, exist_ok=True)

    errors_path = output_dir / f"top_errors_{timestamp}.csv"

    result = validation_df[["Store", "Date", "Sales"]].copy()

    result["predicted_sales"] = predictions
    result["absolute_error"] = (result["Sales"] - result["predicted_sales"]).abs()

    result = result.rename(columns={"Sales": "actual_sales"})

    result = result.sort_values("absolute_error", ascending=False).head(top_n)

    result.to_csv(errors_path, index=False)

    logger.info(f"Top errors saved at {errors_path}")

def save_experiment_summary(
    metrics: dict,
    features_used: list,
    model_name: str,
    train_rows: int,
    validation_rows: int,
    artifacts_dir: Path,
    timestamp: str,
    promotion_audit: dict | None = None,
):
    """
    Save consolidated experiment metadata.
    """

    logger.info("Saving experiment summary artifact.")

    experiment_summary = {
        "timestamp": timestamp,
        "model": model_name,
        "features_used": features_used,
        "train_rows": train_rows,
        "validation_rows": validation_rows,
        "metrics": {
            "MAE": metrics["MAE"],
            "RMSE": metrics["RMSE"],
        },
    }

    if promotion_audit is not None:
        experiment_summary["promotion_audit"] = promotion_audit

    output_path = artifacts_dir / f"experiment_summary_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(experiment_summary, f, indent=4)

    logger.info(f"Experiment summary saved at {output_path}")

def save_error_by_store(
    validation_ready,
    predictions,
    artifacts_dir: Path,
    timestamp: str,
):
    """
    Save aggregated error diagnostics by store.
    """

    logger.info("Saving error by store artifact.")

    diagnostics = validation_ready[["Store"]].copy()
    diagnostics["absolute_error"] = abs(
        validation_ready["Sales"].values - predictions
    )

    error_by_store = (
        diagnostics.groupby("Store")
        .agg(
            mean_absolute_error=("absolute_error", "mean"),
            max_absolute_error=("absolute_error", "max"),
            observations=("absolute_error", "count"),
        )
        .reset_index()
        .sort_values("mean_absolute_error", ascending=False)
    )

    output_path = artifacts_dir / f"error_by_store_{timestamp}.csv"

    error_by_store.to_csv(output_path, index=False)

    logger.info(f"Error by store saved at {output_path}")

def update_benchmark_history(
    metrics: dict,
    features_used: list,
    model_name: str,
    train_rows: int,
    validation_rows: int,
    artifacts_dir: Path,
    timestamp: str,
    promotion_audit: dict | None = None,
):
    """
    Append current experiment to benchmark history.
    """

    logger.info("Updating benchmark history artifact.")

    benchmark_path = artifacts_dir / "benchmark_history.csv"

    benchmark_entry = {
        "timestamp": timestamp,
        "model": model_name,
        "features_used": "|".join(features_used),
        "MAE": metrics["MAE"],
        "RMSE": metrics["RMSE"],
        "train_rows": train_rows,
        "validation_rows": validation_rows,
    }

    if promotion_audit is not None:
        benchmark_entry.update(
            {
                "promoted_to_champion": promotion_audit["promoted"],
                "promotion_reason_code": promotion_audit.get("reason_code"),
                "champion_before": promotion_audit["champion_before"],
                "champion_after": promotion_audit["champion_after"],
                "promotion_metric": promotion_audit["metric"],
                "promotion_direction": promotion_audit.get("direction"),
                "challenger_metric_value": promotion_audit["challenger_metric_value"],
                "champion_metric_value": promotion_audit["champion_metric_value"],
                "absolute_improvement": promotion_audit.get("absolute_improvement"),
                "relative_improvement": promotion_audit.get("relative_improvement"),
                "min_absolute_improvement": promotion_audit.get("min_absolute_improvement"),
                "min_relative_improvement": promotion_audit.get("min_relative_improvement"),
            }
        )

    benchmark_row = pd.DataFrame([benchmark_entry])

    if benchmark_path.exists():
        existing = pd.read_csv(benchmark_path)
        benchmark_row = pd.concat([existing, benchmark_row], ignore_index=True)

    benchmark_row.to_csv(benchmark_path, index=False)

    logger.info(f"Benchmark history updated at {benchmark_path}")

def save_promotion_report(
    artifacts_dir: Path,
    window: int = 50,
) -> None:
    """
    Build an explainability-friendly promotion report from benchmark history.
    """

    logger.info("Saving promotion explainability report.")

    benchmark_path = artifacts_dir / "benchmark_history.csv"
    output_path = artifacts_dir / "promotion_report_latest.json"

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "window": window,
        "status": "ok",
    }

    if not benchmark_path.exists():
        report.update(
            {
                "status": "benchmark_history_missing",
                "total_runs": 0,
                "audited_runs": 0,
                "promotion_rate": None,
                "reason_code_distribution": {},
                "latest_decision": None,
            }
        )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Promotion report saved at {output_path}")
        return

    try:
        history = pd.read_csv(benchmark_path)
    except pd.errors.EmptyDataError:
        history = pd.DataFrame()

    if history.empty:
        report.update(
            {
                "status": "benchmark_history_empty",
                "total_runs": 0,
                "audited_runs": 0,
                "promotion_rate": None,
                "reason_code_distribution": {},
                "latest_decision": None,
            }
        )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Promotion report saved at {output_path}")
        return

    recent = history.tail(window).copy()

    required_columns = [
        "promoted_to_champion",
        "promotion_reason_code",
        "promotion_metric",
        "promotion_direction",
        "challenger_metric_value",
        "champion_metric_value",
        "absolute_improvement",
        "relative_improvement",
        "min_absolute_improvement",
        "min_relative_improvement",
        "champion_before",
        "champion_after",
        "timestamp",
    ]

    missing_columns = [col for col in required_columns if col not in recent.columns]

    if missing_columns:
        report.update(
            {
                "status": "missing_audit_columns",
                "missing_columns": missing_columns,
                "total_runs": int(len(history)),
                "audited_runs": 0,
                "promotion_rate": None,
                "reason_code_distribution": {},
                "latest_decision": None,
            }
        )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Promotion report saved at {output_path}")
        return

    audited = recent.dropna(subset=["promotion_reason_code"]).copy()

    if audited.empty:
        report.update(
            {
                "total_runs": int(len(history)),
                "audited_runs": 0,
                "promotion_rate": None,
                "reason_code_distribution": {},
                "latest_decision": None,
            }
        )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Promotion report saved at {output_path}")
        return

    promoted_numeric = pd.to_numeric(audited["promoted_to_champion"], errors="coerce")
    promotion_rate = float(promoted_numeric.mean()) if not promoted_numeric.isna().all() else None

    reason_distribution = (
        audited["promotion_reason_code"]
        .value_counts()
        .to_dict()
    )

    latest = audited.iloc[-1]

    latest_promoted_raw = latest["promoted_to_champion"]
    if isinstance(latest_promoted_raw, str):
        latest_promoted = latest_promoted_raw.strip().lower() in {"true", "1", "yes"}
    else:
        latest_promoted = bool(latest_promoted_raw)

    report.update(
        {
            "total_runs": int(len(history)),
            "audited_runs": int(len(audited)),
            "promotion_rate": promotion_rate,
            "reason_code_distribution": reason_distribution,
            "latest_decision": {
                "timestamp": latest["timestamp"],
                "promoted": latest_promoted,
                "reason_code": latest["promotion_reason_code"],
                "metric": latest["promotion_metric"],
                "direction": latest["promotion_direction"],
                "challenger_metric_value": latest["challenger_metric_value"],
                "champion_metric_value": latest["champion_metric_value"],
                "absolute_improvement": latest["absolute_improvement"],
                "relative_improvement": latest["relative_improvement"],
                "min_absolute_improvement": latest["min_absolute_improvement"],
                "min_relative_improvement": latest["min_relative_improvement"],
                "champion_before": latest["champion_before"],
                "champion_after": latest["champion_after"],
            },
        }
    )

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)

    logger.info(f"Promotion report saved at {output_path}")

def save_feature_importance(
    importance_df: pd.DataFrame,
    artifacts_dir: Path,
    timestamp: str,
    ):
    """
    Save feature importance artifact.
    """

    logger.info("Saving feature importance artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    output_path = artifacts_dir / f"feature_importance_{timestamp}.csv"

    importance_df.to_csv(output_path, index=False)

    logger.info(f"Feature importance saved at {output_path}")

def save_inference_predictions(
    predictions: pd.DataFrame,
    timestamp: str
) -> None:
    """
    Save inference predictions artifact.
    """

    logger.info("Saving inference predictions artifact.")

    output_path = Path(
        f"artifacts/inference_predictions_{timestamp}.csv"
    )

    predictions.to_csv(output_path, index=False)

    logger.info(f"Inference predictions saved at {output_path}")

def save_drift_report(
    report: dict,
    artifacts_dir: Path,
) -> None:
    """
    Save latest inference drift monitoring report.
    """

    logger.info("Saving drift report artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    output_path = artifacts_dir / "drift_report_latest.json"

    with open(output_path, "w") as file:
        json.dump(report, file, indent=4)

    logger.info(f"Drift report saved at {output_path}")

def save_governance_summary(
    artifacts_dir: Path,
) -> None:
    """
    Save unified governance observability summary for operational consumption.
    """

    logger.info("Saving governance observability summary.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    registry_path = Path("config/model_registry.yaml")
    promotion_report_path = artifacts_dir / "promotion_report_latest.json"
    drift_report_path = artifacts_dir / "drift_report_latest.json"
    benchmark_path = artifacts_dir / "benchmark_history.csv"
    output_path = artifacts_dir / "governance_summary_latest.json"

    registry = {}

    if registry_path.exists():
        with open(registry_path, "r") as file:
            loaded = yaml.safe_load(file)
            if isinstance(loaded, dict):
                registry = loaded

    champion_model = registry.get("champion_model")
    champion_metrics = load_champion_metrics(registry)

    promotion_report = None
    if promotion_report_path.exists():
        with open(promotion_report_path, "r") as file:
            promotion_report = json.load(file)

    drift_report = None
    if drift_report_path.exists():
        with open(drift_report_path, "r") as file:
            drift_report = json.load(file)

    latest_benchmark = None

    if benchmark_path.exists():
        try:
            history = pd.read_csv(benchmark_path)
        except pd.errors.EmptyDataError:
            history = pd.DataFrame()

        if not history.empty:
            latest = history.iloc[-1]

            latest_benchmark = {
                "timestamp": latest.get("timestamp"),
                "model": latest.get("model"),
                "features_used": latest.get("features_used"),
                "MAE": float(latest["MAE"]) if pd.notna(latest.get("MAE")) else None,
                "RMSE": float(latest["RMSE"]) if pd.notna(latest.get("RMSE")) else None,
            }

    latest_decision = None if promotion_report is None else promotion_report.get("latest_decision")
    drift_model_filename = None if drift_report is None else drift_report.get("model_filename")

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "champion": {
            "model_filename": champion_model,
            "metrics": None
            if champion_metrics is None
            else {
                "MAE": champion_metrics.get("MAE"),
                "RMSE": champion_metrics.get("RMSE"),
            },
        },
        "promotion": {
            "report_status": "promotion_report_missing"
            if promotion_report is None
            else promotion_report.get("status"),
            "latest_decision": latest_decision,
        },
        "drift": {
            "report_status": "drift_report_missing"
            if drift_report is None
            else drift_report.get("status"),
            "drift_detected": None
            if drift_report is None
            else drift_report.get("drift_detected"),
            "model_filename": drift_model_filename,
            "drifted_features": []
            if drift_report is None
            else drift_report.get("drifted_features", []),
            "baseline_resolution_source": None
            if drift_report is None
            else drift_report.get("baseline_resolution_source"),
            "baseline_expected_filename": None
            if drift_report is None
            else drift_report.get("baseline_expected_filename"),
            "baseline_resolved_filename": None
            if drift_report is None
            else drift_report.get("baseline_resolved_filename"),
        },
        "latest_benchmark": latest_benchmark,
        "consistency_checks": {
            "promotion_aligned_to_registry": None
            if champion_model is None or latest_decision is None
            else latest_decision.get("champion_after") == champion_model,
            "drift_aligned_to_registry": None
            if champion_model is None or drift_model_filename is None
            else drift_model_filename == champion_model,
        },
    }

    with open(output_path, "w") as file:
        json.dump(summary, file, indent=4)

    logger.info(f"Governance observability summary saved at {output_path}")


def save_governance_alerts(
    artifacts_dir: Path,
    consecutive_rejection_threshold: int = 3,
    critical_drift_feature_threshold: int = 5,
    recurrent_baseline_backfill_threshold: int = 3,
) -> None:
    """
    Save governance alerts derived from unified observability summary.
    """

    logger.info("Saving governance alerts artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    summary_path = artifacts_dir / "governance_summary_latest.json"
    benchmark_path = artifacts_dir / "benchmark_history.csv"
    output_path = artifacts_dir / "governance_alerts_latest.json"

    alerts = []

    if not summary_path.exists():
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "summary_missing",
            "alerts": [
                {
                    "code": "GOVERNANCE_SUMMARY_MISSING",
                    "severity": "critical",
                    "message": "Governance summary artifact not found.",
                    "details": {
                        "summary_path": str(summary_path),
                    },
                }
            ],
            "total_alerts": 1,
            "critical_alerts": 1,
            "warn_alerts": 0,
            "info_alerts": 0,
        }

        with open(output_path, "w") as file:
            json.dump(payload, file, indent=4)

        logger.info(f"Governance alerts saved at {output_path}")
        return

    with open(summary_path, "r") as file:
        summary = json.load(file)

    promotion = summary.get("promotion", {})
    drift = summary.get("drift", {})
    consistency_checks = summary.get("consistency_checks", {})

    promotion_status = promotion.get("report_status")
    drift_status = drift.get("report_status")
    drift_detected = drift.get("drift_detected")
    drifted_features = drift.get("drifted_features", [])
    baseline_resolution_source = drift.get("baseline_resolution_source")

    if promotion_status == "promotion_report_missing":
        alerts.append(
            {
                "code": "PROMOTION_REPORT_MISSING",
                "severity": "warn",
                "message": "Promotion report is missing.",
                "details": {},
            }
        )

    if drift_status == "drift_report_missing":
        alerts.append(
            {
                "code": "DRIFT_REPORT_MISSING",
                "severity": "warn",
                "message": "Drift report is missing.",
                "details": {},
            }
        )

    if drift_status == "baseline_missing":
        alerts.append(
            {
                "code": "DRIFT_BASELINE_MISSING",
                "severity": "warn",
                "message": "Drift baseline is missing for the active champion model.",
                "details": {
                    "model_filename": drift.get("model_filename"),
                },
            }
        )

    if isinstance(baseline_resolution_source, str) and baseline_resolution_source.startswith("backfill_from"):
        backfill_streak = 1
        archive_metrics_dir = Path("archive") / "metrics"

        if archive_metrics_dir.exists():
            archived_reports = sorted(
                archive_metrics_dir.glob("drift_report_*.json"),
                reverse=True,
            )

            for report_path in archived_reports:
                try:
                    with open(report_path, "r") as file:
                        archived_report = json.load(file)
                except (json.JSONDecodeError, OSError):
                    continue

                archived_source = archived_report.get("baseline_resolution_source")
                if isinstance(archived_source, str) and archived_source.startswith("backfill_from"):
                    backfill_streak += 1
                else:
                    break

        if backfill_streak >= recurrent_baseline_backfill_threshold:
            alerts.append(
                {
                    "code": "BASELINE_BACKFILL_RECURRENT",
                    "severity": "warn",
                    "message": "Baseline resolution is repeatedly relying on backfill.",
                    "details": {
                        "consecutive_backfill_count": backfill_streak,
                        "threshold": recurrent_baseline_backfill_threshold,
                        "latest_resolution_source": baseline_resolution_source,
                        "expected_baseline_filename": drift.get("baseline_expected_filename"),
                        "resolved_baseline_filename": drift.get("baseline_resolved_filename"),
                    },
                }
            )

    if drift_detected is True:
        drifted_count = len(drifted_features)
        severity = "critical" if drifted_count >= critical_drift_feature_threshold else "warn"

        alerts.append(
            {
                "code": "DRIFT_DETECTED",
                "severity": severity,
                "message": "Inference drift detected for one or more model input features.",
                "details": {
                    "drifted_feature_count": drifted_count,
                    "drifted_features": drifted_features,
                    "critical_threshold": critical_drift_feature_threshold,
                },
            }
        )

    if consistency_checks.get("promotion_aligned_to_registry") is False:
        alerts.append(
            {
                "code": "PROMOTION_REGISTRY_MISMATCH",
                "severity": "critical",
                "message": "Promotion decision is not aligned with current champion registry.",
                "details": {
                    "promotion_aligned_to_registry": False,
                },
            }
        )

    if consistency_checks.get("drift_aligned_to_registry") is False:
        alerts.append(
            {
                "code": "DRIFT_REGISTRY_MISMATCH",
                "severity": "critical",
                "message": "Drift report model is not aligned with current champion registry.",
                "details": {
                    "drift_aligned_to_registry": False,
                },
            }
        )

    consecutive_rejections = 0

    if benchmark_path.exists():
        try:
            benchmark = pd.read_csv(benchmark_path)
        except pd.errors.EmptyDataError:
            benchmark = pd.DataFrame()

        if not benchmark.empty and "promotion_reason_code" in benchmark.columns:
            for _, row in benchmark.iloc[::-1].iterrows():
                reason = row.get("promotion_reason_code")
                if not isinstance(reason, str) or not reason.startswith("REJECTED"):
                    break
                consecutive_rejections += 1

    if consecutive_rejections >= consecutive_rejection_threshold:
        alerts.append(
            {
                "code": "CONSECUTIVE_PROMOTION_REJECTIONS",
                "severity": "warn",
                "message": "Consecutive promotion rejections reached configured threshold.",
                "details": {
                    "consecutive_rejections": consecutive_rejections,
                    "threshold": consecutive_rejection_threshold,
                },
            }
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok",
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_alerts": sum(1 for alert in alerts if alert["severity"] == "critical"),
        "warn_alerts": sum(1 for alert in alerts if alert["severity"] == "warn"),
        "info_alerts": sum(1 for alert in alerts if alert["severity"] == "info"),
    }

    with open(output_path, "w") as file:
        json.dump(payload, file, indent=4)

    logger.info(f"Governance alerts saved at {output_path}")


def save_governance_panel_snapshot(
    artifacts_dir: Path,
) -> None:
    """
    Save dashboard-friendly governance snapshot for operational consumption.
    """

    logger.info("Saving governance panel snapshot artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    summary_path = artifacts_dir / "governance_summary_latest.json"
    alerts_path = artifacts_dir / "governance_alerts_latest.json"
    output_path = artifacts_dir / "governance_panel_latest.json"

    summary = {}
    alerts = {}

    if summary_path.exists():
        with open(summary_path, "r") as file:
            loaded = json.load(file)
            if isinstance(loaded, dict):
                summary = loaded

    if alerts_path.exists():
        with open(alerts_path, "r") as file:
            loaded = json.load(file)
            if isinstance(loaded, dict):
                alerts = loaded

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "champion_model": summary.get("champion", {}).get("model_filename"),
        "champion_metrics": summary.get("champion", {}).get("metrics"),
        "promotion_status": summary.get("promotion", {}).get("report_status"),
        "promotion_latest_decision": summary.get("promotion", {}).get("latest_decision"),
        "drift_status": summary.get("drift", {}).get("report_status"),
        "drift_detected": summary.get("drift", {}).get("drift_detected"),
        "drifted_features": summary.get("drift", {}).get("drifted_features", []),
        "drift_baseline_resolution_source": summary.get("drift", {}).get("baseline_resolution_source"),
        "drift_baseline_expected_filename": summary.get("drift", {}).get("baseline_expected_filename"),
        "drift_baseline_resolved_filename": summary.get("drift", {}).get("baseline_resolved_filename"),
        "consistency_checks": summary.get("consistency_checks"),
        "alerts_total": alerts.get("total_alerts", 0),
        "alerts_critical": alerts.get("critical_alerts", 0),
        "alerts_warn": alerts.get("warn_alerts", 0),
        "alerts_info": alerts.get("info_alerts", 0),
    }

    with open(output_path, "w") as file:
        json.dump(payload, file, indent=4)

    logger.info(f"Governance panel snapshot saved at {output_path}")


def save_powerbi_export(
    artifacts_dir: Path,
) -> None:
    """
    Save flat CSV export of governance panel for Power BI consumption.
    Reads governance_panel_latest.json and flattens all nested fields
    into a single-row CSV consumable directly by Power BI as a table.
    """

    logger.info("Saving Power BI flat export artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    panel_path = artifacts_dir / "governance_panel_latest.json"
    output_path = artifacts_dir / "powerbi_export_latest.csv"

    if not panel_path.exists():
        logger.warning("governance_panel_latest.json not found. Skipping Power BI export.")
        return

    with open(panel_path, "r") as file:
        panel = json.load(file)

    decision = panel.get("promotion_latest_decision") or {}
    metrics = panel.get("champion_metrics") or {}
    consistency = panel.get("consistency_checks") or {}
    drifted_features = panel.get("drifted_features") or []

    row = {
        "generated_at": panel.get("generated_at"),
        "champion_model": panel.get("champion_model"),
        "champion_mae": metrics.get("MAE"),
        "champion_rmse": metrics.get("RMSE"),
        "promotion_status": panel.get("promotion_status"),
        "promotion_reason_code": decision.get("reason_code"),
        "promotion_promoted": decision.get("promoted"),
        "promotion_challenger_mae": decision.get("challenger_metric_value"),
        "promotion_champion_before": decision.get("champion_before"),
        "promotion_champion_after": decision.get("champion_after"),
        "drift_status": panel.get("drift_status"),
        "drift_detected": panel.get("drift_detected"),
        "drifted_features_count": len(drifted_features),
        "drift_baseline_resolution_source": panel.get("drift_baseline_resolution_source"),
        "drift_baseline_expected_filename": panel.get("drift_baseline_expected_filename"),
        "drift_baseline_resolved_filename": panel.get("drift_baseline_resolved_filename"),
        "consistency_promotion_aligned": consistency.get("promotion_aligned_to_registry"),
        "consistency_drift_aligned": consistency.get("drift_aligned_to_registry"),
        "alerts_total": panel.get("alerts_total", 0),
        "alerts_critical": panel.get("alerts_critical", 0),
        "alerts_warn": panel.get("alerts_warn", 0),
        "alerts_info": panel.get("alerts_info", 0),
    }

    pd.DataFrame([row]).to_csv(output_path, index=False)

    logger.info(f"Power BI flat export saved at {output_path}")

def save_powerbi_benchmark_export(
    artifacts_dir: Path,
) -> None:
    """
    Save flat CSV export of benchmark history for Power BI trend consumption.
    Reads benchmark_history.csv and produces a renamed, BI-friendly version
    with explicit column names and stable analytical types.
    Skips silently if benchmark_history.csv does not exist or is empty.
    """

    logger.info("Saving Power BI benchmark history export artifact.")

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    source_path = artifacts_dir / "benchmark_history.csv"
    output_path = artifacts_dir / "powerbi_benchmark_export_latest.csv"

    if not source_path.exists():
        logger.warning("benchmark_history.csv not found. Skipping Power BI benchmark export.")
        return

    try:
        df = pd.read_csv(source_path)
    except pd.errors.EmptyDataError:
        logger.warning("benchmark_history.csv is empty. Skipping Power BI benchmark export.")
        return

    if df.empty or "timestamp" not in df.columns:
        logger.warning("benchmark_history.csv has no usable rows. Skipping Power BI benchmark export.")
        return

    required_columns = {"timestamp", "model", "MAE", "RMSE"}
    if not required_columns.issubset(df.columns):
        logger.warning("benchmark_history.csv missing required columns. Skipping Power BI benchmark export.")
        return

    run_datetime = pd.to_datetime(
        df["timestamp"],
        format="%Y%m%d_%H%M%S",
        errors="coerce",
    )

    promoted = (
        df.get("promoted_to_champion")
        .fillna(False)
        .astype(bool)
        if "promoted_to_champion" in df.columns
        else pd.Series(False, index=df.index)
    )

    export = pd.DataFrame()
    export["run_timestamp"] = df["timestamp"]
    export["run_datetime"] = run_datetime.dt.strftime("%Y-%m-%dT%H:%M:%S")
    export["model_name"] = df.get("model")
    export["features_used"] = df.get("features_used")
    export["train_rows"] = df.get("train_rows")
    export["validation_rows"] = df.get("validation_rows")
    export["mae"] = df.get("MAE")
    export["rmse"] = df.get("RMSE")
    export["promoted"] = promoted
    export["promotion_reason_code"] = df.get("promotion_reason_code")
    export["champion_before"] = df.get("champion_before")
    export["champion_after"] = df.get("champion_after")
    export["challenger_mae"] = df.get("challenger_metric_value")
    export["champion_mae_at_decision"] = df.get("champion_metric_value")
    export["absolute_improvement"] = df.get("absolute_improvement")
    export["relative_improvement"] = df.get("relative_improvement")

    export.to_csv(output_path, index=False)

    logger.info(f"Power BI benchmark history export saved at {output_path}")

def load_champion_metrics(registry: dict) -> dict | None:
    """
    Load metrics artifact associated with the current champion model.
    Looks in active artifacts first, then archive fallback.
    Returns None if no champion is registered or metrics file is not found.
    """

    champion = registry.get("champion_model")

    if not champion or champion == "latest":
        return None

    model_stem = Path(champion).stem

    if not model_stem.startswith("model_"):
        logger.info(f"Champion model name does not follow expected pattern: {champion}")
        return None

    timestamp = model_stem[len("model_"):]
    metrics_filename = f"metrics_{timestamp}.json"

    candidate_paths = [
        Path("artifacts") / metrics_filename,
        Path("archive") / "metrics" / metrics_filename,
    ]

    for metrics_path in candidate_paths:
        if metrics_path.exists():
            with open(metrics_path, "r") as file:
                return json.load(file)

    logger.info(
        f"Champion metrics file not found in active or archive folders: {metrics_filename}"
    )
    return None

def load_distribution_baseline_for_model(model_filename: str) -> dict | None:
    """
    Load distribution baseline artifact aligned to a specific model filename.
    Looks in active artifacts first, then archive fallback.
    If exact baseline is missing, backfill from latest available baseline.
    """

    model_stem = Path(model_filename).stem

    if not model_stem.startswith("model_"):
        logger.info(f"Model filename does not follow expected pattern: {model_filename}")
        return None

    timestamp = model_stem[len("model_"):]
    baseline_filename = f"distribution_baseline_{timestamp}.json"

    artifacts_dir = Path("artifacts")
    archive_metrics_dir = Path("archive") / "metrics"

    expected_path = artifacts_dir / baseline_filename

    candidate_paths = [
        ("exact_active", expected_path),
        ("exact_archive", archive_metrics_dir / baseline_filename),
    ]

    for source, baseline_path in candidate_paths:
        if baseline_path.exists():
            with open(baseline_path, "r") as file:
                baseline = json.load(file)

            baseline["baseline_resolution_source"] = source
            baseline["baseline_expected_filename"] = baseline_filename
            baseline["baseline_resolved_filename"] = baseline_path.name
            return baseline

    # Backfill policy: use latest available baseline and materialize
    # expected filename in active artifacts for champion-aligned lookup.
    fallback_candidates = sorted(artifacts_dir.glob("distribution_baseline_*.json"))
    fallback_source = "backfill_from_active"

    if not fallback_candidates:
        fallback_candidates = sorted(
            archive_metrics_dir.glob("distribution_baseline_*.json")
        )
        fallback_source = "backfill_from_archive"

    if fallback_candidates:
        source_path = fallback_candidates[-1]
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, expected_path)

        logger.info(
            "Backfilled missing distribution baseline for model %s | source=%s | target=%s",
            model_filename,
            source_path.name,
            expected_path.name,
        )

        with open(expected_path, "r") as file:
            baseline = json.load(file)

        baseline["baseline_resolution_source"] = fallback_source
        baseline["baseline_expected_filename"] = baseline_filename
        baseline["baseline_resolved_filename"] = source_path.name
        return baseline

    logger.info(
        "Distribution baseline file not found in active or archive folders: %s",
        baseline_filename,
    )
    return None

def evaluate_promotion(
    new_metrics: dict,
    current_metrics: dict | None,
    policy: dict
) -> dict:
    """
    Evaluate promotion decision and return a structured decision trace.
    """

    metric = policy.get("metric", "MAE")
    direction = policy.get("direction", "lower")
    min_relative_improvement = float(policy.get("min_relative_improvement", 0.0))
    min_absolute_improvement = float(policy.get("min_absolute_improvement", 0.0))

    if metric not in new_metrics:
        raise KeyError(f"Metric '{metric}' missing in challenger metrics.")

    challenger_value = float(new_metrics[metric])

    decision = {
        "metric": metric,
        "direction": direction,
        "challenger_metric_value": challenger_value,
        "champion_metric_value": None,
        "absolute_improvement": None,
        "relative_improvement": None,
        "min_absolute_improvement": min_absolute_improvement,
        "min_relative_improvement": min_relative_improvement,
        "promoted": False,
        "reason_code": "UNSET",
    }

    if current_metrics is None:
        decision["promoted"] = True
        decision["reason_code"] = "NO_CHAMPION_BASELINE"
        logger.info(
            "Promotion decision | reason=%s | metric=%s | challenger=%.6f | promoted=%s",
            decision["reason_code"],
            metric,
            challenger_value,
            decision["promoted"],
        )
        return decision

    if metric not in current_metrics:
        raise KeyError(f"Metric '{metric}' missing in champion metrics.")

    champion_value = float(current_metrics[metric])
    decision["champion_metric_value"] = champion_value

    if direction == "lower":
        absolute_improvement = champion_value - challenger_value
        baseline = champion_value
    elif direction == "higher":
        absolute_improvement = challenger_value - champion_value
        baseline = abs(champion_value)
    else:
        raise ValueError("promotion_policy.direction must be 'lower' or 'higher'.")

    if baseline == 0:
        relative_improvement = float("inf") if absolute_improvement > 0 else 0.0
    else:
        relative_improvement = absolute_improvement / baseline

    promoted = (
        absolute_improvement >= min_absolute_improvement
        and relative_improvement >= min_relative_improvement
    )

    if promoted:
        reason_code = "PROMOTED_THRESHOLD_MET"
    elif absolute_improvement < min_absolute_improvement and relative_improvement < min_relative_improvement:
        reason_code = "REJECTED_ABSOLUTE_AND_RELATIVE"
    elif absolute_improvement < min_absolute_improvement:
        reason_code = "REJECTED_ABSOLUTE_THRESHOLD"
    else:
        reason_code = "REJECTED_RELATIVE_THRESHOLD"

    decision.update(
        {
            "absolute_improvement": absolute_improvement,
            "relative_improvement": relative_improvement,
            "promoted": promoted,
            "reason_code": reason_code,
        }
    )

    logger.info(
        "Promotion decision | reason=%s | metric=%s | current=%.6f | challenger=%.6f | abs_impr=%.6f | rel_impr=%.6f | abs_thr=%.6f | rel_thr=%.6f | promoted=%s",
        reason_code,
        metric,
        champion_value,
        challenger_value,
        absolute_improvement,
        relative_improvement,
        min_absolute_improvement,
        min_relative_improvement,
        promoted,
    )

    return decision

def should_promote(
    new_metrics: dict,
    current_metrics: dict | None,
    policy: dict
) -> bool:
    """
    Backward-compatible boolean promotion check.
    """

    decision = evaluate_promotion(
        new_metrics=new_metrics,
        current_metrics=current_metrics,
        policy=policy,
    )
    return decision["promoted"]


def update_champion_model(model_filename: str) -> None:
    """
    Update champion model registry after successful training.
    Preserve existing governamence keys in the registry.
    """
    
    registry_path = Path("config/model_registry.yaml")
    registry = {}

    if registry_path.exists():
        with open(registry_path, "r") as file:
            loaded = yaml.safe_load(file)
            if isinstance(loaded, dict):
                registry = loaded
            
    registry["champion_model"] = model_filename

    with open(registry_path, "w") as file:
        yaml.safe_dump(registry, file, sort_keys=False)

    logger.info(
        f"Champion model updated to {model_filename}"
    )
