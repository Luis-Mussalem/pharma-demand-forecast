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
    Preserves champion model and its metrics file when skip_model is provided.
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

    folder_mapping = {
        "model_": "models",
        "metrics_": "metrics",
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
                "champion_before": promotion_audit["champion_before"],
                "champion_after": promotion_audit["champion_after"],
                "promotion_metric": promotion_audit["metric"],
                "challenger_metric_value": promotion_audit["challenger_metric_value"],
                "champion_metric_value": promotion_audit["champion_metric_value"],
            }
        )

    benchmark_row = pd.DataFrame([benchmark_entry])

    if benchmark_path.exists():
        existing = pd.read_csv(benchmark_path)
        benchmark_row = pd.concat([existing, benchmark_row], ignore_index=True)

    benchmark_row.to_csv(benchmark_path, index=False)

    logger.info(f"Benchmark history updated at {benchmark_path}")

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
    Decide if challenger should be promoted to champion based on metric policy.
    """

    if current_metrics is None:
        logger.info("No champion metrics found. Challenger will be promoted.")
        return True

    metric = policy.get("metric", "MAE")
    direction = policy.get("direction", "lower")
    min_relative_improvement = float(policy.get("min_relative_improvement", 0.0))
    min_absolute_improvement = float(policy.get("min_absolute_improvement", 0.0))

    if metric not in new_metrics:
        raise KeyError(f"Metric '{metric}' missing in challenger metrics.")
    if metric not in current_metrics:
        raise KeyError(f"Metric '{metric}' missing in champion metrics.")

    new_value = float(new_metrics[metric])
    current_value = float(current_metrics[metric])

    if direction == "lower":
        absolute_improvement = current_value - new_value
        baseline = current_value
    elif direction == "higher":
        absolute_improvement = new_value - current_value
        baseline = abs(current_value)
    else:
        raise ValueError("promotion_policy.direction must be 'lower' or 'higher'.")

    if baseline == 0:
        relative_improvement = float("inf") if absolute_improvement > 0 else 0.0
    else:
        relative_improvement = absolute_improvement / baseline

    promote = (
        absolute_improvement >= min_absolute_improvement
        and relative_improvement >= min_relative_improvement
    )

    logger.info(
        "Promotion decision | metric=%s | current=%.6f | new=%.6f | abs_impr=%.6f | rel_impr=%.6f | promote=%s",
        metric,
        current_value,
        new_value,
        absolute_improvement,
        relative_improvement,
        promote,
    )

    return promote


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
