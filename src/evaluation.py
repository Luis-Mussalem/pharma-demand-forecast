from __future__ import annotations

import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from tornado.locale import get

from src.logger import get_logger
from src.training import (
    prepare_modeling_data,
    prepare_features,
    encode_categorical_features
)

logger = get_logger()

def evaluate_model(model, validation_df: pd.DataFrame) -> dict:
    """
    Evaluate trained model on validation dataset.
    """

    logger.info("Starting model evaluation.")

    validation_df = prepare_modeling_data(validation_df)

    X_val, y_val = prepare_features(validation_df)

    X_val = encode_categorical_features(X_val)

    logger.info("Generating validation predictions. This may take a moment...")
    
    predictions = model.predict(X_val)

    mae = mean_absolute_error(y_val, predictions)
    rmse = root_mean_squared_error(y_val, predictions)

    metrics = {
        "MAE": mae,
        "RMSE": rmse
    }

    logger.info(f"Validation MAE: {mae:.2f}")
    logger.info(f"Validation RMSE: {rmse:.2f}")

    logger.info("Model evaluation completed successfully.")

    return metrics