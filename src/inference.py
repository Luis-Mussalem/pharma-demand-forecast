import joblib
import pandas as pd

from pathlib import Path

from src.logger import get_logger
from src.training import prepare_features, encode_categorical_features

logger = get_logger()

def validate_inference_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate inference input schema before preprocessing.
    """

    logger.info("Validating inference input schema.")

    required_columns = [
        "Store",
        "DayOfWeek",
        "Date",
        "Customers",
        "Open",
        "Promo",
        "StateHoliday",
        "SchoolHoliday"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required inference columns: {missing_columns}"
        )

    if "Sales" in df.columns:
        logger.info("Sales column detected in inference input and removed.")
        df = df.drop(columns=["Sales"])

    logger.info("Inference schema validated successfully.")

    return df

def get_latest_model_path() -> str:
    """
    Retrieve latest trained model artifact automatically.
    """

    artifact_dir = Path("artifacts")

    model_files = sorted(
        artifact_dir.glob("model_*.pkl")
    )

    if not model_files:
        raise FileNotFoundError("No trained model artifact found.")

    latest_model = model_files[-1]

    logger.info(f"Latest model detected: {latest_model}")

    return str(latest_model)

def load_model(model_path: str = None):
    """
    Load trained model artifact from disk.
    """

    if model_path is None:
        model_path = get_latest_model_path()

    logger.info(f"Loading model from {model_path}")

    model = joblib.load(model_path)

    logger.info("Model loaded successfully.")

    return model


def prepare_inference_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare inference feature matrix using training-compatible preprocessing.
    """

    logger.info("Preparing inference dataset.")

    df = validate_inference_schema(df)

    X, _ = prepare_features(df)

    X = encode_categorical_features(X)

    logger.info("Inference dataset ready.")

    return X


def run_inference(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Run prediction using loaded model.
    """

    logger.info("Running inference.")

    X = prepare_inference_data(df)

    valid_index = X.dropna().index

    X = X.loc[valid_index]
    
    df = df.loc[valid_index]

    predictions = model.predict(X)
    predictions = predictions.clip(min=0)

    result = df.copy()
    result["predicted_sales"] = predictions

    logger.info("Inference completed successfully.")

    return result