# Pharma Demand Forecast — Data Engineering Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Pipeline](https://img.shields.io/badge/Data%20Pipeline-Modular-green)
![Architecture](https://img.shields.io/badge/Architecture-Data%20Engineering-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Project Overview

This project implements a modular and reproducible machine learning pipeline for daily sales forecasting using the Rossmann Store Sales dataset.

The goal is not only predictive performance, but also production-oriented ML architecture with explicit ownership of responsibilities, fail-fast contracts, and governed artifact lifecycle.

The pipeline enforces:

- explicit data contracts
- schema validation
- temporal consistency
- modular feature engineering
- deterministic execution
- artifact versioning
- inference reproducibility
- explainable model promotion governance

---

## Architecture Highlights

Main architectural principles:

- YAML-driven execution
- strict validation before transformations
- schema contract versioning
- explicit champion model governance
- benchmark-aware promotion policy
- explainable promotion decision trace
- champion-aligned drift baseline and inference drift monitoring
- temporal split before feature generation
- modular feature registry
- isolated training and inference pipelines
- timestamped artifact persistence
- automatic artifact archiving
- config-driven runtime paths

This architecture follows production-oriented ML pipeline patterns and separates data responsibilities across explicit pipeline layers.

---

## Current Pipeline Scope

### Data Layer

- Controlled ingestion with explicit dtype handling
- Schema and granularity validation (`Store + Date`)
- Temporal split with leakage prevention

### Feature Layer

- Calendar features
- Lag features
- Rolling statistics
- Promo signal activation through feature registry

### Modeling Layer

Supported models:

- `RandomForestRegressor`
- `HistGradientBoostingRegressor`

Current best baseline:

- `HistGradientBoostingRegressor`
- MAE ≈ 508
- RMSE ≈ 779

### Evaluation Layer

Generated artifacts:

- metrics
- validation predictions
- top prediction errors
- store-level error aggregation
- feature importance
- benchmark history
- experiment summary with promotion audit

### Inference Layer

Dedicated prediction pipeline through predict.py:

- registry-governed champion loading (explicit champion file or latest policy)
- inference schema validation
- historical context reconstruction
- config-driven inference input
- prediction artifact persistence
- inference artifact archiving
- champion-aligned baseline loading for drift comparison
- non-blocking drift detection and drift report persistence
- schema-versioned inference contract validation

The current pipeline supports full train → evaluation → artifact → inference execution.

---

# Pipeline Architecture

The pipeline follows a modular architecture designed to enforce data contracts, prevent temporal leakage, and ensure reproducible CLI execution.

```text
                ┌─────────────────────────┐
                │         main.py         │
                │  Pipeline Orchestration │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │     config_loader.py    │
                │   Load YAML Config      │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │   model_registry.yaml   │
                │  Champion Model Policy  │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │    schema_registry.py   │
                │ Contract Definitions    │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │       ingestion.py      │
                │   Controlled Data Load  │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │       validation.py     │
                │   Training Contract     │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │       splitting.py      │
                │ Temporal Train Split    │
                └────────────┬────────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
  ┌─────────────────────┐     ┌──────────────────────────┐
  │   processing.py     │     │      processing.py       │
  │ train feature set   │     │ validation with history  │
  └──────────┬──────────┘     └────────────┬─────────────┘
             │                             │
             └─────────────┬───────────────┘
                           ▼
                ┌─────────────────────────┐
                │       training.py       │
                │ readiness + encoding    │
                │ baseline model fit      │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │      evaluation.py      │
                │ MAE + RMSE validation   │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │      artifacts.py       │
                │ persistence + archive   │
                │ diagnostics + benchmark │
                │ promotion governance    │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ inference_validation.py │
                │ Inference Contract      │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │       predict.py        │
                │ separate inference flow │
                └─────────────────────────┘
```

Each module has a clearly defined responsibility:

- main.py — CLI entry point and pipeline orchestration
- config_loader.py — external configuration loader
- ingestion.py — controlled dataset loading
- validation.py — schema and granularity enforcement
- schema_registry.py — explicit schema contracts for training and inference
- inference_validation.py — isolated inference contract enforcement
- splitting.py — deterministic temporal train-validation split
- processing.py — feature engineering pipeline (calendar, lag, rolling features)
- feature_registry.py — config-driven feature orchestration
- training.py — modeling preparation and baseline fitting
- evaluation.py — validation scoring and prediction generation
- drift.py — distribution baseline computation and inference drift detection
- artifacts.py — artifact lifecycle, promotion policy, explainable decision trace, benchmark persistence, drift artifacts
- predict.py — isolated inference execution using registry-governed champion model

---

# Repository Structure
```
pharma-demand-forecast/
│
├── AGENTS.md
├── README.md
├── main.py
├── predict.py
├── requirements.txt
│
├── archive/
│   ├── diagnostics/
│   ├── metrics/
│   ├── models/
│   └── predictions/
│
├── artifacts/
│   ├── benchmark_history.csv
│   ├── model_YYYYMMDD_HHMMSS.pkl
│   ├── metrics_YYYYMMDD_HHMMSS.json
│   ├── predictions_YYYYMMDD_HHMMSS.csv
│   ├── top_errors_YYYYMMDD_HHMMSS.csv
│   ├── error_by_store_YYYYMMDD_HHMMSS.csv
│   ├── experiment_summary_YYYYMMDD_HHMMSS.json
│   ├── feature_importance_YYYYMMDD_HHMMSS.csv
│   ├── promotion_report_latest.json
│   ├── distribution_baseline_YYYYMMDD_HHMMSS.json
│   ├── drift_report_latest.json
│   ├── governance_summary_latest.json
│   ├── governance_alerts_latest.json
│   ├── governance_panel_latest.json
│   ├── powerbi_export_latest.csv
│   ├── powerbi_benchmark_export_latest.csv
│   └── inference_predictions_YYYYMMDD_HHMMSS.csv
│
├── config/
│   ├── pipeline_config.yaml
│   ├── schema_version.yaml
│   └── model_registry.yaml
│
├── data/
│   ├── inference/
│   │   └── future_data.csv
│   └── raw/
│       ├── train.csv
│       ├── test.csv
│       └── store.csv
│
├── docs/
│   ├── engineering_decisions.md
│   ├── data_dictionary.md
│   └── archive/
│       └── backup_readme.md
│
├── logs/
│   └── pipeline.log
│
├── notebooks/
│   └── exploration.ipynb
│
├── powerbi/
│   ├── governance_panel_contract.md
│   ├── benchmark_history_contract.md
│   └── pharma_governance_dashboard.pbix
│
├── src/
│   ├── __init__.py
│   ├── artifacts.py
│   ├── config_loader.py
│   ├── drift.py
│   ├── evaluation.py
│   ├── feature_registry.py
│   ├── importance.py
│   ├── inference.py
│   ├── inference_validation.py
│   ├── ingestion.py
│   ├── logger.py
│   ├── processing.py
│   ├── schema_registry.py
│   ├── splitting.py
│   ├── training.py
│   └── validation.py
│
└── tests/
    ├── test_drift_monitoring.py
    ├── test_model_governance.py
    └── test_promotion_policy.py
```

---

## Documentation
Detailed technical decisions, trade-offs and architectural evolution are documented in:
**docs/engineering_decisions.md**

---

## Project Status

- Champion governance: model_registry.yaml
- Promotion policy: benchmark-aware and threshold-based
- Promotion decision explainability: evaluate_promotion in src/artifacts.py
- Compatibility wrapper preserved: should_promote delegates to evaluate_promotion
- Promotion audit persisted in experiment_summary_YYYYMMDD_HHMMSS.json and benchmark_history.csv
- Promotion report artifact: artifacts/promotion_report_latest.json
- Champion baseline metrics loaded from active artifacts with archive fallback
- Archive rotation preserves active champion model and champion baseline metrics
- Distribution baseline persisted per training run: artifacts/distribution_baseline_YYYYMMDD_HHMMSS.json
- Inference drift report persisted as latest runtime signal: artifacts/drift_report_latest.json
- Drift baseline lookup is aligned to the active model consumed in inference
- Drift baseline resolution metadata persisted in drift report:
  - baseline_resolution_source
  - baseline_expected_filename
  - baseline_resolved_filename
- Baseline resolution paths supported:
  - exact_active
  - exact_archive
  - backfill_from_active
  - backfill_from_archive
- Unified governance observability snapshot persisted: artifacts/governance_summary_latest.json
- Governance alerts artifact persisted: artifacts/governance_alerts_latest.json
- Dashboard-friendly governance panel snapshot persisted: artifacts/governance_panel_latest.json
- Governance alerts support configurable thresholds via runtime config
- Regression tests cover promotion, drift, model governance, panel snapshot, and configurable alert threshold
- Flat CSV export for Power BI consumption persisted: artifacts/powerbi_export_latest.csv
- Power BI semantic contract defined: powerbi/governance_panel_contract.md
- Flat benchmark history export for Power BI trend consumption persisted: artifacts/powerbi_benchmark_export_latest.csv
- Benchmark history semantic contract defined: powerbi/benchmark_history_contract.md

### Verification (recommended)

- python -m unittest discover -s tests -p "test_drift_monitoring.py" -v
- python -m unittest discover -s tests -p "test_model_governance.py" -v
- python -m unittest discover -s tests -p "test_promotion_policy.py" -v
- python main.py --config config/pipeline_config.yaml
- python predict.py --config config/pipeline_config.yaml

---

# Planned Pipeline Evolution

Next stages of the project include:

- Power BI dashboard visuals over powerbi_export_latest.csv and powerbi_benchmark_export_latest.csv (snapshot + trend ready)
- store-level drift segmentation and monitoring
- alert thresholds by feature family with policy profiles
- unified observability layer for promotion and drift lifecycle trends

---

# Quick Start

Repository:

https://github.com/Luis-Mussalem/pharma-demand-forecast

Clone the repository and run the pipeline:

```bash
git clone https://github.com/Luis-Mussalem/pharma-demand-forecast.git
cd pharma-demand-forecast
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py --config pipeline_config.yaml
python predict.py --config pipeline_config.yaml

---

# Author

Luis Mussalem