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
    Preserves the current champion model file when skip_model is provided.
    """

    logger.info("Archiving previous artifacts.")

    artifacts_dir = Path("artifacts")
    archive_dir = Path("archive")

    folder_mapping = {
        "model_": "models",
        "metrics_": "metrics",
        "experiment_summary_": "metrics",
        "feature_importance_": "metrics",
        "predictions_": "predictions",
        "top_errors_": "diagnostics",
        "error_by_store_": "diagnostics"
    }

    for file_path in artifacts_dir.iterdir():

        if file_path.name == "benchmark_history.csv":
            continue

        if skip_model and file_path.name == skip_model:
            logger.info(f"Retaining champion model in artifacts: {file_path.name}")
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
):
    """
    Append current experiment to benchmark history.
    """

    logger.info("Updating benchmark history artifact.")

    benchmark_path = artifacts_dir / "benchmark_history.csv"

    benchmark_row = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "model": model_name,
                "features_used": "|".join(features_used),
                "MAE": metrics["MAE"],
                "RMSE": metrics["RMSE"],
                "train_rows": train_rows,
                "validation_rows": validation_rows,
            }
        ]
    )

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
    Returns None if no champion is registered or metrics file is not found.
    """

    champion = registry.get("champion_model")

    if not champion or champion == "latest":
        return None

    name = Path(champion).stem
    timestamp = name[len("model_"):]
    metrics_path = Path("artifacts") / f"metrics_{timestamp}.json"

    if not metrics_path.exists():
        logger.info(f"Champion metrics file not found: {metrics_path}")
        return None

    with open(metrics_path, "r") as file:
        return json.load(file)

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
