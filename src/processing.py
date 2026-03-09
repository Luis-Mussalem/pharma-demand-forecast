from __future__ import annotations

import pandas as pd

from src.logger import get_logger

logger = get_logger()


def create_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate calendar-based features from the Date column.
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

def create_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create rolling window statistics for Sales grouped by Store.
    """

    logger.info("Generating rolling window features.")

    df = df.copy()

    df = df.sort_values(["Store", "Date"])

    sales_group = df.groupby("Store")["Sales"]

    df["rolling_mean_sales_7"] = (
        sales_group.shift(1).rolling(7).mean()
    )

    df["rolling_mean_sales_14"] = (
        sales_group.shift(1).rolling(14).mean()
    )

    df["rolling_std_sales_7"] = (
        sales_group.shift(1).rolling(7).std()
    )

    logger.info("Rolling window features generated successfully.")

    return df

def create_promo_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preserve promotion signal as model feature.
    """

    logger.info("Generating promo feature.")

    logger.info("Promo feature generated successfully.")

    return df