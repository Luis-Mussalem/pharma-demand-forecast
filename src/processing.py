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

def run_feature_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Execute the full feature engineering pipeline.

    This function orchestrates all feature transformations in the correct order.
    """

    logger.info("Starting feature engineering pipeline.")

    df = df.copy()

    df = df.sort_values(["Store", "Date"])

    df = create_calendar_features(df)

    df = create_lag_features(df)

    df = create_rolling_features(df)

    logger.info("Feature engineering pipeline completed successfully.")

    return df

def generate_validation_features(
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    max_lag: int = 7
) -> pd.DataFrame:
    """
    Generate validation features using historical context from the train dataset.

    This prevents losing lag information at the boundary between
    train and validation sets.
    """

    logger.info("Generating validation features with historical context.")

    # Retrieve last observations from training set
    train_tail = train_df.groupby("Store").tail(max_lag)

    # Concatenate train history with validation
    validation_with_history = pd.concat(
        [train_tail, validation_df],
        axis=0
    )

    # Run feature pipeline
    validation_with_history = run_feature_pipeline(validation_with_history)

    # Remove historical rows
    validation_features = validation_with_history.loc[
        validation_with_history["Date"].isin(validation_df["Date"])
    ]

    logger.info("Validation features generated successfully.")

    return validation_features