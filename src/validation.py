import pandas as pd
from pandas.api.types import (
    is_dtype_equal,
    is_categorical_dtype,
)
from src.logger import get_logger
from pathlib import Path
from src.config_loader import load_schema_version
from src.schema_registry import TRAINING_SCHEMA_V1

logger = get_logger()

SCHEMA_CONFIG = load_schema_version(Path("config/schema_version.yaml"))

EXPECTED_COLUMNS = TRAINING_SCHEMA_V1["columns"]

EXPECTED_DTYPES = TRAINING_SCHEMA_V1["dtypes"]

def validate_columns(df: pd.DataFrame) -> None:
    """
    Validates whether the dataset contains exactly the expected columns.
    Raises an error if columns are missing or unexpected columns exist.
    """
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)

    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    if extra_cols:
        raise ValueError(f"Unexpected columns: {extra_cols}")


def validate_dtypes(df: pd.DataFrame) -> None:
    """
    Validates if dataset columns have expected data types.
    """

    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        raise TypeError("Column 'Date' must be datetime")

    for column, expected_dtype in EXPECTED_DTYPES.items():
        if column == "Date":
            continue

        actual_dtype = df[column].dtype

        # Special handling for categorical
        if expected_dtype == "category":
            if not is_categorical_dtype(df[column]):
                raise TypeError(
                    f"Column '{column}' must be categorical."
                )
            continue

        expected_dtype_obj = pd.Series([], dtype=expected_dtype).dtype

        if not is_dtype_equal(actual_dtype, expected_dtype_obj):
            raise TypeError(
                f"Column '{column}' has dtype '{actual_dtype}' "
                f"but expected '{expected_dtype_obj}'"
            )

def validate_granularity(df: pd.DataFrame) -> None:
    """
    Ensures there are no duplicate records for Store + Date.
    """
    duplicates = df.duplicated(subset=["Store", "Date"]).sum()

    if duplicates > 0:
        raise ValueError(
            f"Dataset contains {duplicates} duplicate Store-Date records."
        )


def validate_dataset(df: pd.DataFrame) -> None:
    """
    Runs all validation checks.
    """
    logger.info(f"Starting dataset validation using schema."
                f"{SCHEMA_CONFIG['training_schema']}..."    
            )

    validate_columns(df)
    validate_dtypes(df)
    validate_granularity(df)

    logger.info("Dataset validation passed successfully.") 