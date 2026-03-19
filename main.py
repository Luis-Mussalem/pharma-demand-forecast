import argparse
from pathlib import Path
import sys

from src.ingestion import load_data
from src.logger import get_logger
from src.config_loader import load_config
from src.splitting import temporal_train_validation_split
from src.training import (
    train_model,
    prepare_modeling_data,
    prepare_features,
    encode_categorical_features,
)
from src.evaluation import evaluate_model
from src.artifacts import (
    archive_previous_artifacts,
    save_feature_importance,
    save_model,
    save_metrics,
    save_distribution_baseline,
    save_predictions,
    save_top_errors,
    save_error_by_store,
    save_experiment_summary,
    save_promotion_report,
    generate_timestamp,
    update_benchmark_history,
    update_champion_model,
    evaluate_promotion,
    should_promote,
    load_champion_metrics,
)
from src.feature_registry import (
    run_feature_pipeline,
    generate_validation_features,
    FEATURE_REGISTRY,
)
from src.importance import compute_feature_importance
from src.drift import compute_distribution_baseline

def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """

    parser = argparse.ArgumentParser(
        description="Pharma Demand Forecast - Data Pipeline Entry Point"
    )

    parser.add_argument(
    "--config",
    type=str,
    required=True,
    help="Path to pipeline configuration YAML file."
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
    )

    parser.add_argument(
    "--save-processed",
    action="store_true",
    help="If provided, saves processed dataset to output path.",
    )

    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save processed dataset.",
    )

    return parser.parse_args()

def configure_logger(log_level: str):
    """
    Configure logger level dynamically
    """

    logger = get_logger()
    logger.setLevel(log_level)

    return logger

def main():

    args = parse_arguments()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)

    logger = configure_logger(args.log_level)

    logger.info("Pipeline execution started.")
    logger.debug(f"Parsed arguments: {args}")

    try:

        data_path = Path(config["data"]["raw_data_path"]).resolve()

        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found at {data_path}")

        df = load_data(data_path)

        logger.info(f"Dataset successfully loaded. Shape: {df.shape}.")

        train_df, validation_df = temporal_train_validation_split(
            df, split_date=config["split"]["split_date"]
        )

        logger.info("Temporal split completed successfully.")
        logger.info(f"Train dataset shape: {train_df.shape}")
        logger.info(f"Validation dataset shape: {validation_df.shape}")

        feature_config = config["features"]
        features_used = [
            feature_name
            for feature_name in FEATURE_REGISTRY
            if feature_config.get(feature_name, False)
        ]

        train_df = run_feature_pipeline(train_df, feature_config)
        
        validation_df = generate_validation_features(
            train_df,
            validation_df,
            feature_config
        )

        logger.info("Feature engineering completed successfully.")

        train_ready = prepare_modeling_data(train_df)
        X_train, _ = prepare_features(train_ready)
        X_train = encode_categorical_features(X_train)
        distribution_baseline = compute_distribution_baseline(X_train)

        model = train_model(
            train_df,
            config["model"]["name"]
        )

        logger.info(f"Model trained successfully: {config['model']['name']}")

        metrics, predictions, validation_ready = evaluate_model(model, validation_df)
        importance_df = compute_feature_importance(model, validation_df)
        metrics["features_used"] = features_used
        metrics["model"] = config["model"]["name"]

        logger.info(f"Model evaluation metrics: {metrics}")

        artifacts_dir = Path("artifacts")
        artifact_timestamp = generate_timestamp()

        registry = load_config(Path("config/model_registry.yaml"))
        current_champion_metrics = load_champion_metrics(registry)

        archive_previous_artifacts(
            skip_model=registry.get("champion_model")
        )

        save_model(model, artifacts_dir, artifact_timestamp)

        save_distribution_baseline(
        baseline=distribution_baseline,
        artifacts_dir=artifacts_dir,
        timestamp=artifact_timestamp,
        )

        promotion_decision = evaluate_promotion(
            new_metrics=metrics,
            current_metrics=current_champion_metrics,
            policy=registry.get("promotion_policy", {}),
        )

        promoted = promotion_decision["promoted"]

        challenger_model_name = f"model_{artifact_timestamp}.pkl"
        champion_before = registry.get("champion_model")

        if promoted:
            update_champion_model(challenger_model_name)
            champion_after = challenger_model_name
        else:
            logger.info(
                "Challenger did not meet promotion criteria. Champion retained: %s | reason=%s",
                champion_before,
                promotion_decision["reason_code"],
            )
            champion_after = champion_before

        promotion_audit = {
            "promoted": promoted,
            "reason_code": promotion_decision["reason_code"],
            "champion_before": champion_before,
            "champion_after": champion_after,
            "metric": promotion_decision["metric"],
            "direction": promotion_decision["direction"],
            "challenger_metric_value": promotion_decision["challenger_metric_value"],
            "champion_metric_value": promotion_decision["champion_metric_value"],
            "absolute_improvement": promotion_decision["absolute_improvement"],
            "relative_improvement": promotion_decision["relative_improvement"],
            "min_absolute_improvement": promotion_decision["min_absolute_improvement"],
            "min_relative_improvement": promotion_decision["min_relative_improvement"],
        }

        save_metrics(metrics, artifacts_dir, artifact_timestamp)
        save_predictions(validation_ready, predictions, artifacts_dir, artifact_timestamp)
        save_top_errors(validation_ready, predictions, artifacts_dir, artifact_timestamp)
        save_error_by_store(
            validation_ready,
            predictions,
            artifacts_dir,
            artifact_timestamp,
        )
        save_experiment_summary(
            metrics=metrics,
            features_used=features_used,
            model_name=config["model"]["name"],
            train_rows=len(train_df),
            validation_rows=len(validation_df),
            artifacts_dir=artifacts_dir,
            timestamp=artifact_timestamp,
            promotion_audit=promotion_audit,
        )
        update_benchmark_history(
            metrics=metrics,
            features_used=features_used,
            model_name=config["model"]["name"],
            train_rows=len(train_df),
            validation_rows=len(validation_df),
            artifacts_dir=artifacts_dir,
            timestamp=artifact_timestamp,
            promotion_audit=promotion_audit,
        )
        save_promotion_report(
            artifacts_dir=artifacts_dir,
            window=50,
        )
        save_feature_importance(
            importance_df,
            artifacts_dir,
            artifact_timestamp
        )

        if args.save_processed:
            if args.output_path is None:
                raise ValueError(
                    "If --save-processed is used, --output-path must be provided."
                )
            
            output_path = Path(args.output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

            train_df.to_csv(output_path / "train_processed.csv", index=False)
            validation_df.to_csv(output_path / "validation_processed.csv", index=False)
            logger.info(f"Processed dataset saved to {output_path}")
        
        logger.info("Pipeline execution completed successfully.")

    except Exception:
        logger.exception("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()


