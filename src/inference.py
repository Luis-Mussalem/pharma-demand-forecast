import joblib
import pandas as pd

from pathlib import Path

from src.logger import get_logger
from src.training import prepare_features, encode_categorical_features
from src.feature_registry import run_feature_pipeline
from src.config_loader import load_config
from src.inference_validation import validate_inference_schema

logger = get_logger()

def get_latest_model_path() -> str:
    """
    Retrieve latest trained model artifact automatically.
    """

    registry = load_config(Path("config/model_registry.yaml"))

    champion_model = registry["champion_model"]

    if champion_model != "latest":
        model_path = Path("artifacts") / champion_model

        if not model_path.exists():
            raise FileNotFoundError(
                f"Champion model not found: {model_path}"
            )

        logger.info(f"Champion model selected: {model_path}")

        return str(model_path)

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

def build_inference_context(future_df: pd.DataFrame, history_window: int) -> pd.DataFrame:
    """
    Concatenate recent historiccal observations to support lag fearture generation.
    """

    history = pd.read_csv(
        "data/raw/train.csv",
        parse_dates=["Date"],
        dtype={"StateHoliday": str},
    )

    history = history.sort_values(["Store", "Date"])

    recent_history = (
        history.groupby("Store")
        .tail(history_window)
    )

    combined = pd.concat(
        [recent_history, future_df],
        ignore_index=True
    )

    return combined

def prepare_inference_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare inference feature matrix using training-compatible preprocessing.
    """

    logger.info("Preparing inference dataset.")

    config = load_config(Path("config/pipeline_config.yaml"))

    df = validate_inference_schema(df)

    future_size = len(df)
    
    history_window = config["inference"]   ["history_window_days"]

    df = build_inference_context(df, history_window)
    
    feature_config = config["features"] 
    
    df = run_feature_pipeline(df, feature_config)

    df = df.tail(future_size)

    df = (
        df.sort_values(["Store", "Date"])
            .groupby("Store")
            .head(1)
    )

    if "Id" in df.columns:
            df = df.drop(columns=["Id"])

    X, _ = prepare_features(df)

    X = encode_categorical_features(X)

    rolling_columns = [
    "rolling_mean_sales_7",
    "rolling_mean_sales_14",
    "rolling_std_sales_7"
    ]

    X[rolling_columns] = X[rolling_columns].fillna(0)

    aligned_df = df.loc[X.index]

    logger.info(f"Final inference matrix shape: {X.shape}")

    return X, aligned_df


def run_inference(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Run prediction using loaded model.
    """

    logger.info("Running inference.")

    X, df = prepare_inference_data(df)

    predictions = model.predict(X)
    predictions = predictions.clip(min=0)

    result = df.copy()
    result["predicted_sales"] = predictions

    logger.info("Inference completed successfully.")

    return result, X