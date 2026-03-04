import pandas as pd
from src.logger import get_logger

logger = get_logger()


def temporal_train_validation_split(
    df: pd.DataFrame,
    split_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform deterministic temporal train-validation split.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset containing a Date column.

    split_date : str
        Date used as the last training observation.

    Returns
    -------
    train_df : pd.DataFrame
    validation_df : pd.DataFrame
    """

    logger.info("Starting temporal train-validation split.")

    if "Date" not in df.columns:
        raise ValueError("Dataset must contain 'Date' column for temporal splitting.")

    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        raise TypeError("Column 'Date' must be datetime for temporal splitting.")

    # Sort explicitly
    df = df.sort_values("Date")

    split_timestamp = pd.to_datetime(split_date)

    train_df = df[df["Date"] <= split_timestamp]
    validation_df = df[df["Date"] > split_timestamp]

    if train_df.empty:
        raise ValueError("Train dataset is empty after split.")

    if validation_df.empty:
        raise ValueError("Validation dataset is empty after split.")

    # Safety check for leakage
    max_train_date = train_df["Date"].max()
    min_validation_date = validation_df["Date"].min()

    if max_train_date >= min_validation_date:
        raise RuntimeError("Temporal leakage detected in split.")

    logger.info(
        f"Train period: {train_df['Date'].min()} → {train_df['Date'].max()}"
    )

    logger.info(
        f"Validation period: {validation_df['Date'].min()} → {validation_df['Date'].max()}"
    )

    logger.info(f"Train shape: {train_df.shape}")
    logger.info(f"Validation shape: {validation_df.shape}")

    return train_df, validation_df
    