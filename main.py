import argparse
from pathlib import Path
import sys

from src.ingestion import load_data
from src.logger import get_logger

def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """

    parser = argparse.ArgumentParser(
        description="Pharma Demand Forecast - Data Pipeline Entry Point"
    )

    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to raw input dataset (CSV)"
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
    
    logger = configure_logger(args.log_level)

    logger.info("Pipeline execution started.")
    logger.debug(f"Parsed arguments: {args}")

    try:
        data_path = Path(args.data_path).resolve()

        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found at {data_path}")
        
        df = load_data(data_path)

        logger.info(f"Dataset successfully loaded. Shape: {df.shape}.")

        if args.save_processed:
            if args.output_path is None:
                raise ValueError(
                    "If --save-processed is used, --output-path must be provided."
                )
            
            output_path = Path(args.output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(output_path, index=False)
            logger.info(f"Processed dataset saved to {output_path}")
        
        logger.info("Pipeline execution completed successfully.")

    except Exception:
        logger.exception("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
        

