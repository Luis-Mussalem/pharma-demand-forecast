import pandas as pd

from src.logger import setup_logger
logger = setup_logger()

EXPECTED_COLUMNS = [
    "Store",
    "DayOfWeek",
    "Date",
    "Sales",
    "Customers",
    "Open",
    "Promo",
    "StateHoliday",
    "SchoolHoliday",
]


EXPECTED_DTYPES = {
    "Store": "int64",
    "DayOfWeek": "int64",
    "Date": "datetime64[ns]",
    "Sales": "int64",
    "Customers": "int64",
    "Open": "int64",
    "Promo": "int64",
    "StateHoliday": "category",
    "SchoolHoliday": "int64",
}


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

    # Validate Date separately (more flexible)
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        raise TypeError("Column 'Date' must be datetime")

    for column, expected_dtype in EXPECTED_DTYPES.items():
        if column == "Date":
            continue

        actual_dtype = str(df[column].dtype)

        if actual_dtype != expected_dtype:
            raise TypeError(
                f"Column '{column}' has dtype '{actual_dtype}' but expected '{expected_dtype}'"
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
    logger.info("Starting dataset validation...")

    validate_columns(df)
    validate_dtypes(df)
    validate_granularity(df)

    logger.info("Dataset validation passed successfully.")