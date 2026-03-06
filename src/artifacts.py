import json
import joblib

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