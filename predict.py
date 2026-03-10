from pathlib import Path

from src.ingestion import load_data
from src.config_loader import load_config
from src.feature_registry import run_feature_pipeline
from src.inference import load_model, run_inference
from src.logger import get_logger


logger = get_logger()


def main():
    """
    Run standalone inference pipeline.
    """

    logger.info("Inference pipeline started.")

    config = load_config(Path("config/pipeline_config.yaml"))

    data_path = config["data"]["raw_data_path"]

    df = load_data(data_path)

    df = run_feature_pipeline(
        df,
        config["features"]
    )

    model = load_model()

    predictions = run_inference(model, df)

    logger.info("Inference pipeline completed successfully.")

    print(predictions.head())


if __name__ == "__main__":
    main()

