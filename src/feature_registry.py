import pandas as pd

from src.processing import (
    create_calendar_features,
    create_lag_features,
    create_promo_feature,
    create_rolling_features,
)
from src.logger import get_logger

logger = get_logger()

FEATURE_REGISTRY = {
    "calendar": create_calendar_features,
    "lag": create_lag_features,
    "rolling": create_rolling_features,
    "promo": create_promo_feature,
}


def run_feature_pipeline(df, feature_config):
    """
    Executes feature engineering pipeline according to external config.
    """

    for feature_name, feature_function in FEATURE_REGISTRY.items():

        enabled = feature_config.get(feature_name, False)

        if enabled:
            logger.info(f"Applying feature: {feature_name}")
            df = feature_function(df)
        else:
            logger.info(f"Skipping feature: {feature_name}")

    return df

def generate_validation_features(train_df, validation_df, feature_config):

    history = train_df.groupby("Store").tail(14)

    combined = pd.concat([history, validation_df], axis=0)

    combined = run_feature_pipeline(combined, feature_config)

    validation_result = combined.iloc[len(history):]

    return validation_result