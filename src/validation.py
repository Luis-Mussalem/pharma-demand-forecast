import pandas as pd
from pandas.api.types import (
    is_dtype_equal,
    is_categorical_dtype,
)
from src.logger import get_logger

logger = get_logger()

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
    logger.info("Starting dataset validation...")

    validate_columns(df)
    validate_dtypes(df)
    validate_granularity(df)

    logger.info("Dataset validation passed successfully.") 