import argparse

from pathlib import Path
from datetime import datetime

from src.ingestion import load_data
from src.config_loader import load_config
from src.inference import load_model, run_inference
from src.logger import get_logger
from src.artifacts import (
    archive_inference_artifacts,
    save_inference_predictions,
)

logger = get_logger()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True,
        help="Path to pipeline config file."
    )

    return parser.parse_args()

def main():
    """
    Run standalone inference pipeline.
    """

    logger.info("Inference pipeline started.")

    args = parse_args()

    config = load_config(Path(args.config))

    data_path = config["inference"]["data_path"]

    df = load_data(data_path, validate=False)

    model = load_model()

    predictions = run_inference(model, df)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    archive_inference_artifacts()

    save_inference_predictions(
        predictions,
        timestamp
    )

    logger.info("Inference pipeline completed successfully.")


if __name__ == "__main__":
    main()

