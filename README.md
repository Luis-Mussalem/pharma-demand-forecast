# Pharma Demand Forecast — Data Engineering Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Pipeline](https://img.shields.io/badge/Data%20Pipeline-Modular-green)
![Architecture](https://img.shields.io/badge/Architecture-Data%20Engineering-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Project Overview

This project implements a modular and reproducible machine learning pipeline for daily sales forecasting using the Rossmann Store Sales dataset.

The primary goal is not only predictive performance, but the construction of a production-oriented architecture that enforces:

- explicit data contracts  
- schema validation  
- temporal consistency  
- modular feature engineering  
- deterministic execution  
- artifact versioning  
- inference reproducibility  

The project is designed to demonstrate practical data engineering discipline applied to forecasting workflows, with emphasis on architecture, traceability, and controlled ML lifecycle execution.

---

## Architecture Highlights

Main architectural principles:

- YAML-driven execution  
- strict validation before transformations
- lightweight schema version governance
- lightweight champion model governance 
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

### Inference Layer

Dedicated prediction pipeline through predict.py:

- registry-governed champion loading (explicit champion file or latest policy)  
- inference schema validation  
- historical context reconstruction  
- config-driven inference input  
- prediction artifact persistence  
- inference artifact archiving
- schema-versioned inference contract validation  

The current pipeline already supports full train → evaluation → artifact → inference execution

---

# Pipeline Architecture

The pipeline follows a modular architecture designed to enforce data contracts, prevent temporal leakage, and ensure reproducible CLI execution.

```
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

- **main.py** — CLI entry point and pipeline orchestration  
- **config_loader.py** — external configuration loader  
- **ingestion.py** — controlled dataset loading  
- **validation.py** — schema and granularity enforcement  
- **schema_registry.py** — explicit schema contracts for training and inference  
- **inference_validation.py** — isolated inference contract enforcement 
- **splitting.py** — deterministic temporal train-validation split  
- **processing.py** — feature engineering pipeline (calendar, lag, rolling features)
- **feature_registry.py** — config-driven feature orchestration  
- **training.py** — modeling preparation and baseline fitting  
- **evaluation.py** — validation scoring and prediction generation  
- **artifacts.py** — versioned persistence, benchmark tracking, diagnostics persistence, artifact archiving and champion promotion
- **predict.py** — isolated inference execution using registry-governed champion model

---

# Repository Structure
```
pharma-demand-forecast/
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
│   └── feature_importance_YYYYMMDD_HHMMSS.csv
│
├── config/
│   ├── pipeline_config.yaml
│   ├── schema_version.yaml
│   └── model_registry.yaml
│
├── data/
│   ├── inference/
│   └── raw/
│
├── docs/
│   ├── engineering_decisions.md
│   └── data_dictionary.md
│
├── logs/
│   └── pipeline.log
│
├── notebooks/
│   └── exploration.ipynb
│
├── src/
│   ├── ingestion.py
│   ├── validation.py
│   ├── inference_validation.py
│   ├── schema_registry.py
│   ├── splitting.py
│   ├── processing.py
│   ├── feature_registry.py
│   ├── training.py
│   ├── evaluation.py
│   ├── artifacts.py
│   ├── importance.py
│   ├── inference.py
│   ├── config_loader.py
│   └── logger.py
│
├── main.py
├── predict.py
├── requirements.txt
└── README.md
```

---

## Documentation
Detailed technical decisions, trade-offs and architectural evolution are documented in:
docs/engineering_decisions.md

---

## Project Status

- Champion Governance: config/model_registry.yaml introduced to record the promoted champion model (champion_model key).
- Training → Promotion: src/artifacts.py updates the registry after successful model save.
- Non-destructive Registry Update: champion update preserves existing governance keys (for example: promotion_mode, notes).
- Inference Consumption: src/inference.py reads config/model_registry.yaml and supports:
  - explicit champion filename (for example: model_YYYYMMDD_HHMMSS.pkl)
  - latest policy (resolve newest artifact in artifacts/)
- Regression Tests: tests/test_model_governance.py protects champion selection and promotion behavior.
- Agent Contract & Decision Log: AGENTS.md and docs/engineering_decisions.md include Day 11 closure updates.

### Verification (recommended)
- Run governance tests:
  - python -m unittest discover -s tests -p "test_model_governance.py" -v
  - Expected outcome: tests pass (OK).
- Optional pipeline smoke:
  - python main.py --config config/pipeline_config.yaml
- Optional inference quick-run:
  - python predict.py --config config/pipeline_config.yaml

---

# Planned Pipeline Evolution

Next stages of the project include:

- Benchmark-aware champion/challenger promotion rules
- Batch inference orchestration
- Simple drift monitoring

---

# Quick Start

Repository:

https://github.com/Luis-Mussalem/pharma-demand-forecast

Clone the repository and run the pipeline:

git clone https://github.com/Luis-Mussalem/pharma-demand-forecast.git

cd pharma-demand-forecast

Run training pipeline:
python main.py --config config/pipeline_config.yaml

Run inference pipeline:
python predict.py --config config/pipeline_config.yaml

---

# Author

Luis Mussalem