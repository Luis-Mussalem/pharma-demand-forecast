from __future__ import annotations

import pandas as pd

from src.logger import get_logger

logger = get_logger()


def create_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate calendar-based features from the Date column.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset containing a Date column.

    Returns
    -------
    pd.DataFrame
        Dataset with calendar features added.
    """

    logger.info("Generating calendar features.")

    df = df.copy()

    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    df["day"] = df["Date"].dt.day
    df["week_of_year"] = df["Date"].dt.isocalendar().week.astype(int)

    logger.info("Calendar features generated successfully.")

    return df

def create_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create lag features for the Sales variable grouped by Store.
    """

    logger.info("Generating lag features.")

    df = df.copy()

    df = df.sort_values(["Store", "Date"])

    df["lag_sales_1"] = df.groupby("Store")["Sales"].shift(1)
    df["lag_sales_7"] = df.groupby("Store")["Sales"].shift(7)

    logger.info("Lag features generated successfully.")

    return df

def run_feature_pipeline(df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Starting feature engineering pipeline.")

    df = create_calendar_features(df)

    df = create_lag_features(df)

    logger.info("Feature engineering pipeline completed successfully.")

    return df