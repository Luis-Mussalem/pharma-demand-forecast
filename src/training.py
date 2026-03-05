from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from src.logger import get_logger

logger = get_logger()


TARGET_COLUMN = "Sales"

EXCLUDED_COLUMNS = [
    "Date"
]

def prepare_training_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare dataset for model training by removing rows with missing values.
    """

    logger.info("Preparing training dataset for modeling.")

    initial_shape = df.shape

    df = df.dropna()

    final_shape = df.shape

    removed_rows = initial_shape[0] - final_shape[0]

    logger.info(f"Rows removed due to missing values: {removed_rows}")
    logger.info(f"Training dataset ready. Shape: {final_shape}")

    return df

def prepare_features(df: pd.DataFrame):
    """
    Separate feature matrix and target variable.
    """

    logger.info("Preparing features and target.")

    X = df.drop(columns=[TARGET_COLUMN] + EXCLUDED_COLUMNS)
    y = df[TARGET_COLUMN]

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target vector shape: {y.shape}")

    return X, y

def encode_categorical_features(X: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categorical features for model compatibility.
    """

    logger.info("Encoding categorical features.")

    X = X.copy()

    categorical_columns = X.select_dtypes(include=["category", "object"]).columns

    if len(categorical_columns) > 0:
        logger.info(f"Categorical columns detected: {list(categorical_columns)}")

        for column in categorical_columns:
            X[column] = X[column].cat.codes

    logger.info("Categorical encoding completed successfully.")

    return X

def train_model(train_df: pd.DataFrame):
    """
    Train baseline forecasting model.
    """

    logger.info("Starting model training.")

    train_df = prepare_training_data(train_df)
    
    X_train, y_train = prepare_features(train_df)

    X_train = encode_categorical_features(X_train)

    model = RandomForestRegressor(
    n_estimators=20,
    max_depth=12,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1
    )

    logger.info("Training model. This may take a moment...")
    
    model.fit(X_train, y_train)

    logger.info("Model training completed successfully.")

    return model
