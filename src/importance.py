import pandas as pd

from sklearn.inspection import permutation_importance

from src.logger import get_logger
from src.training import (
    prepare_modeling_data,
    prepare_features,
    encode_categorical_features,
)

logger = get_logger()


def compute_feature_importance(model, validation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute permutation feature importance using validation data.
    """

    logger.info("Computing feature importance.")

    validation_ready = prepare_modeling_data(validation_df)

    X_val, y_val = prepare_features(validation_ready)

    X_val = encode_categorical_features(X_val)

    result = permutation_importance(
        model,
        X_val,
        y_val,
        n_repeats=5,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )

    importance_df = pd.DataFrame(
        {
            "feature": X_val.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    )

    importance_df = importance_df.sort_values(
        by="importance_mean",
        ascending=False
    )

    logger.info("Feature importance computed successfully.")

    return importance_df