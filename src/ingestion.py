from pathlib import Path
import pandas as pd

from src.validation import validate_dataset
from src.logger import get_logger


logger = get_logger()


CSV_DTYPES = {
    "Store": "int64",
    "DayOfWeek": "int64",
    "Sales": "int64",
    "Customers": "int64",
    "Open": "Int64",
    "Promo": "int64",
    "StateHoliday": "category",
    "SchoolHoliday": "int64",
}

DATE_COLUMNS = ["Date"]


def load_data(file_path: Path, validate=True) -> pd.DataFrame:
    """
    Loads raw CSV data, applies schema enforcement and validation.
    """

    logger.info("Starting data ingestion.")
    logger.info(f"Reading data from {file_path}")

    try:
        df = pd.read_csv(
            file_path,
            dtype=CSV_DTYPES,
            parse_dates=DATE_COLUMNS,
            low_memory=False,
        )

        logger.info("CSV successfully loaded.")

        # Sanity check (defensive programming)
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            raise TypeError("Date column was not parsed as datetime.")

        if validate:
            validate_dataset(df)
    
        logger.info("Dataset validation completed successfully.")

        return df

    except Exception:
        logger.exception("Data ingestion failed.")
        raise
