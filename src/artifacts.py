import json
import joblib
import pandas as pd

from datetime import datetime
from pathlib import Path

from src.logger import get_logger

logger = get_logger()


def generate_timestamp() -> str:
    """
    Generate timestamp for versioned artifact names.
    """

    return datetime.now().strftime("%Y%m%d_%H%M%S")


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
