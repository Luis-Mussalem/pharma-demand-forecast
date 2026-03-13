import pandas as pd

from pathlib import Path

from src.logger import get_logger
from src.config_loader import load_schema_version
from src.schema_registry import INFERENCE_SCHEMA_V1

logger = get_logger()

SCHEMA_CONFIG = load_schema_version(Path("config/schema_version.yaml"))


def validate_inference_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate inference input schema before processing.
    """

    logger.info(f"Validating inference input schema."
                f"{SCHEMA_CONFIG['inference_schema']}."    
            )

    required_columns = INFERENCE_SCHEMA_V1["columns"]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required inference columns: {missing_columns}"
        )
    
    if df[required_columns].isnull().values.any():
        raise ValueError(
            "Inference input contains null values in required columns."
    )

    if not df["DayOfWeek"].between(1, 7).all():
        raise ValueError(
            "DayOfWeek must contain values between 1 and 7."
    )

    if "Sales" in df.columns:
        logger.info("Sales columns detected in inference input and removed.")
        df = df.drop(columns=["Sales"])

    logger.info("Inference schema validated successfully.")

    return df