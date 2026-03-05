import argparse
from pathlib import Path
import sys

from src import logger
from src.ingestion import load_data
from src.logger import get_logger
from src.config_loader import load_config
from src.splitting import temporal_train_validation_split
from src.processing import run_feature_pipeline, generate_validation_features
from src.training import train_model
from src.evaluation import evaluate_model

def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """

    parser = argparse.ArgumentParser(
        description="Pharma Demand Forecast - Data Pipeline Entry Point"
    )

    parser.add_argument(
    "--config",
    type=str,
    required=True,
    help="Path to pipeline configuration YAML file."
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
    )

    parser.add_argument(
    "--save-processed",
    action="store_true",
    help="If provided, saves processed dataset to output path.",
    )

    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save processed dataset.",
    )

    return parser.parse_args()

def configure_logger(log_level: str) :
    """
    Configure logger level dinamicaly
    """

    logger = get_logger()
    logger.setLevel(log_level)

    return logger

def main():

    args = parse_arguments()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)

    logger = configure_logger(args.log_level)

    logger.info("Pipeline execution started.")
    logger.debug(f"Parsed arguments: {args}")

    try:

        data_path = Path(config["data"]["raw_data_path"]).resolve()

        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found at {data_path}")

        df = load_data(data_path)

        logger.info(f"Dataset successfully loaded. Shape: {df.shape}.")

        train_df, validation_df = temporal_train_validation_split(
            df, split_date=config["split"]["split_date"]
        )

        logger.info("Temporal split completed successfully.")
        logger.info(f"Train dataset shape: {train_df.shape}")
        logger.info(f"Validation dataset shape: {validation_df.shape}")

        train_df = run_feature_pipeline(train_df)
        validation_df = generate_validation_features(
            train_df,
            validation_df,
            max_lag=7
            )

        logger.info("Feature engineering completed successfully.")

        model = train_model(train_df)

        logger.info("Baseline model trained successfully.")

        metrics = evaluate_model(model, validation_df)
        logger.info(f"Model evaluation metrics: {metrics}")

        if args.save_processed:
            if args.output_path is None:
                raise ValueError(
                    "If --save-processed is used, --output-path must be provided."
                )
            
            output_path = Path(args.output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

            train_df.to_csv(output_path / "train_processed.csv", index=False)
            validation_df.to_csv(output_path / "validation_processed.csv", index=False)
            logger.info(f"Processed dataset saved to {output_path}")
        
        logger.info("Pipeline execution completed successfully.")

    except Exception:
        logger.exception("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
        

