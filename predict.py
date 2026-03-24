import argparse

from pathlib import Path
from datetime import datetime

from src.ingestion import load_data
from src.config_loader import load_config
from src.inference import get_latest_model_path, load_model, run_inference
from src.drift import detect_drift
from src.logger import get_logger
from src.artifacts import (
    archive_inference_artifacts,
    load_distribution_baseline_for_model,
    save_drift_report,
    save_governance_summary,
    save_governance_alerts,
    save_governance_panel_snapshot,
    save_inference_predictions,
)

logger = get_logger()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True,
        help="Path to pipeline config file."
    )

    return parser.parse_args()


def main():
    """
    Run standalone inference pipeline.
    """

    logger.info("Inference pipeline started.")

    args = parse_args()

    config = load_config(Path(args.config))

    data_path = Path(config["inference"]["data_path"])
    z_score_threshold = float(config["drift"]["z_score_threshold"])

    df = load_data(data_path, validate=False)

    model_path = get_latest_model_path()
    model = load_model(model_path)

    predictions, inference_matrix = run_inference(model, df)

    baseline = load_distribution_baseline_for_model(Path(model_path).name)

    if baseline is None:
        drift_report = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "baseline_missing",
            "drift_detected": None,
            "model_filename": Path(model_path).name,
            "z_score_threshold": z_score_threshold,
            "features_evaluated": 0,
            "drifted_features": [],
            "feature_details": {},
        }
    else:
        drift_report = detect_drift(
            X=inference_matrix,
            baseline=baseline,
            z_score_threshold=z_score_threshold,
        )
        drift_report["model_filename"] = Path(model_path).name
        drift_report["baseline_generated_at"] = baseline.get("generated_at")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    archive_inference_artifacts()

    save_inference_predictions(
        predictions,
        timestamp
    )

    save_drift_report(
        drift_report,
        Path("artifacts"),
    )

    save_governance_summary(
        artifacts_dir=Path("artifacts"),
    )

    save_governance_alerts(
        artifacts_dir=Path("artifacts"),
    )

    save_governance_panel_snapshot(
        artifacts_dir=Path("artifacts"),
    )

    logger.info("Inference pipeline completed successfully.")


if __name__ == "__main__":
    main()