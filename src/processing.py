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


def run_feature_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Execute the full feature engineering pipeline.

    This function orchestrates all feature transformations in the correct order.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    Returns
    -------
    pd.DataFrame
        Dataset with engineered features.
    """

    logger.info("Starting feature engineering pipeline.")

    # Calendar features
    df = create_calendar_features(df)

    logger.info("Feature engineering pipeline completed successfully.")

    return df