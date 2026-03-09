# Pharma Demand Forecast — Data Engineering Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Pipeline](https://img.shields.io/badge/Data%20Pipeline-Modular-green)
![Architecture](https://img.shields.io/badge/Architecture-Data%20Engineering-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Project Overview

This project focuses on designing a **structured and reproducible data engineering pipeline** for daily demand forecasting using the **Rossmann Store Sales dataset**.

The objective is not only predictive performance, but the implementation of a **production-oriented data pipeline architecture** that enforces:

- Explicit data contracts  
- Schema validation  
- Type enforcement  
- Granularity control  
- Temporal data integrity  
- Structured logging  
- Deterministic execution  

The project emphasizes **engineering discipline in data workflows**, moving from exploratory notebooks toward modular, production-ready pipelines.

---

# Architecture Highlights

This project focuses on applying **production-grade engineering principles** to a forecasting workflow.

Key architectural decisions:

- **Configuration-driven pipeline** using YAML
- **Strict data contracts** enforced before transformations
- **Fail-fast validation** to prevent silent data corruption
- **Temporal integrity enforcement** before feature engineering
- **Modular pipeline design** enabling independent testing of components

The architecture mirrors patterns commonly used in **data platforms and ML pipelines in production environments**.

---

# Technical Objectives

- Build a modular pipeline using a `src/` project architecture  
- Enforce strict schema and dtype validation  
- Prevent temporal data leakage in forecasting workflows  
- Implement structured logging for observability  
- Externalize configuration through YAML files  
- Ensure deterministic pipeline execution outside notebooks  

---

# Data Granularity

Unit of analysis:

**Store + Date**

Each row represents the **daily sales performance of a store**.

All transformations and validations enforce this level of aggregation to ensure:

- dataset consistency  
- prevention of duplicate records  
- reliable feature engineering  

Granularity is validated as part of the **data contract layer**.

---

# Current Implementation Status

### ✅ CLI Pipeline Entry Point

- Executable pipeline through `main.py`
- CLI interface implemented with `argparse`
- Pipeline execution configured via `--config`
- Deterministic execution independent of notebook environments

### ✅ External Pipeline Configuration

- Pipeline parameters externalized through `config/pipeline_config.yaml`
- Centralized configuration management
- Enables reproducible experiments and environment-independent execution
- Configuration loaded via `src/config_loader.py`

### ✅ Data Ingestion Layer

- Dedicated ingestion module (`src/ingestion.py`)
- Controlled CSV loading with explicit dtype definitions
- Explicit datetime parsing for temporal fields
- Integration with validation layer

### ✅ Data Contract & Validation Layer

- Expected schema enforcement
- Explicit dtype validation
- Granularity validation (Store + Date uniqueness)
- Fail-fast behavior on invalid datasets

### ✅ Structured Logging System

- Console logging with timestamps and severity levels
- Persistent file logging (`logs/pipeline.log`)
- Project-root-based path resolution
- Modular logger configuration (`src/logger.py`)

### ✅ Temporal Train–Validation Split

- Deterministic time-based split implemented in `src/splitting.py`
- Split date controlled via configuration file
- Protection against temporal data leakage
- Logging of training and validation periods

### ✅ Feature Engineering Pipeline

- Dedicated transformation module (`src/processing.py`)
- Modular feature pipeline architecture
- Calendar-based features
- Lag features grouped by store
- Rolling window statistics

### ✅ Leakage-Safe Validation Feature Generation

- Validation features generated using historical context from training data
- Preserves lag and rolling signals across temporal boundaries
- Prevents feature loss at split transition

### ✅ Training Layer

- Dedicated training module (`src/training.py`)
- Explicit separation between feature matrix and target variable
- Modular model training through a model factory
- Support for multiple algorithms:
  - `RandomForestRegressor`
  - `HistGradientBoostingRegressor`
- Model selection controlled externally through YAML configuration
- Modular training pipeline

### ✅ Training Readiness Layer

- Missing-value removal before model fit
- Logging of removed rows
- Deterministic dataset preparation for training

### ✅ Categorical Encoding for Model Compatibility

- Automatic detection of categorical columns
- Encoding applied before model fitting
- Baseline compatibility with tree-based models

### ✅ Model Evaluation Layer

- Dedicated evaluation module (`src/evaluation.py`)
- Validation predictions generated from trained baseline model
- MAE and RMSE calculated on temporal validation set
- Consistent preprocessing between training and validation data

### ✅ Model Comparison Layer

Two production-safe baseline models are now available through external configuration:

- `RandomForestRegressor`
- `HistGradientBoostingRegressor`

Current comparison with calendar + lag + rolling features:

#### RandomForestRegressor

- **MAE:** 513.96  
- **RMSE:** 802.35  

#### HistGradientBoostingRegressor

- **MAE:** 508.37  
- **RMSE:** 779.23  

Current best baseline:

- **HistGradientBoostingRegressor**

This comparison demonstrated that boosting improves performance mainly by reducing large forecasting errors.

### ✅ Feature Registry Layer

- Dedicated orchestration module (`src/feature_registry.py`)
- Feature activation controlled through YAML configuration
- External control of feature families:
  - calendar
  - lag
  - rolling
- Supports controlled ablation studies

### ✅ Artifact Versioning Layer

- Timestamp-based artifact persistence
- Immutable experiment outputs
- Artifacts generated per execution:
  - model_YYYYMMDD_HHMMSS.pkl
  - metrics_YYYYMMDD_HHMMSS.json

### ✅ Feature Lineage in Metrics

- Metrics artifacts now include:
  - model
  - MAE
  - RMSE
  - features_used

### ✅ Prediction Persistence Layer

- Validation predictions saved automatically
- Artifact includes:
  - Store
  - Date
  - actual_sales
  - predicted_sales
  - absolute_error

### ✅ Error Analysis Layer

- Automatic persistence of top prediction errors
- Top-N largest errors saved per experiment
- Supports model diagnostic analysis

---

# Pipeline Architecture

The pipeline follows a modular architecture designed to enforce data contracts, prevent temporal leakage, and ensure reproducible execution.

CLI Execution  
`python main.py --config config/pipeline_config.yaml`

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
                │       ingestion.py      │
                │   Controlled Data Load  │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │       validation.py     │
                │   Data Contract Layer   │
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
                │ Baseline Performance    │
                │ reproducible benchmark  │
                └─────────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │      artifacts.py       │
                │      model, metrics     │
                │ predictions, top errors │
                └─────────────────────────┘
```

Each module has a clearly defined responsibility:

Each module has a clearly defined responsibility:

- **main.py** — CLI entry point and pipeline orchestration  
- **config_loader.py** — external configuration loader  
- **ingestion.py** — controlled dataset loading  
- **validation.py** — schema and granularity enforcement  
- **splitting.py** — deterministic temporal train-validation split  
- **processing.py** — feature engineering pipeline (calendar, lag, rolling features)
- **feature_registry.py** — config-driven feature orchestration  
- **training.py** — modeling preparation and baseline fitting  
- **evaluation.py** — validation scoring and prediction generation  
- **artifacts.py** — versioned persistence of model, metrics, predictions and top errors

---

# Data Pipeline Guarantees

This pipeline enforces a set of guarantees designed to improve reliability and prevent common issues in data workflows.

**Schema Integrity**

- Required columns are validated before processing  
- Dataset structure must match the expected schema  

**Type Consistency**

- Critical columns enforce explicit dtype definitions  
- Prevents silent errors caused by mixed or inferred types  

**Granularity Enforcement**

- Ensures uniqueness of the `Store + Date` key  
- Prevents duplicated observations and aggregation errors  

**Temporal Integrity**

- Train and validation sets are strictly separated in time  
- Prevents data leakage in forecasting tasks  

**Fail-Fast Validation**

- Pipeline execution stops immediately when validation fails  
- Avoids propagation of corrupted datasets  

**Reproducible Execution**

- Configuration is externalized via YAML  
- Pipeline behavior is deterministic across runs  

These guarantees ensure the dataset entering the modeling stage is **consistent, validated, and leakage-safe**.

---

# Engineering Principles Applied

- Single Responsibility Principle  
- Modular architecture  
- Explicit data contracts  
- Observability through structured logging  
- Deterministic pipeline execution  
- Separation between exploration and production code  

---

# Reproducibility & Design Choices

Several design decisions were made to ensure the pipeline is **fully reproducible**:

- Pipeline parameters are externalized through **YAML configuration**
- Execution does not depend on notebooks
- Data validation runs automatically during ingestion
- Temporal splits are deterministic and configurable
- Logging captures the entire pipeline execution flow

This approach ensures that pipeline runs are **repeatable and auditable**.

---

# Engineering Insights & Challenges

## Dtype Inconsistency (`StateHoliday`)

**Issue**

Pandas raised a `DtypeWarning` due to mixed types in the `StateHoliday` column.

**Resolution**

- Explicit dtype specification during CSV ingestion
- Conversion of `StateHoliday` to categorical type
- Alignment of validation rules with the data contract

**Lesson**

Data contracts should represent **semantic meaning**, not only inferred technical types.

---

## Logging Path Resolution

**Issue**

Logs were written relative to the notebook execution path.

**Resolution**

- Implemented root-path resolution using `__file__`
- Standardized logs in the project-level `logs/` directory

**Lesson**

Production pipelines must not depend on execution context.

---

## Module Reloading During Development

**Issue**

Changes in validation modules were not reflected immediately in notebooks.

**Resolution**

- Used `importlib.reload()` during development
- Reinforced `main.py` as the official execution entry point

**Lesson**

Notebooks are exploratory tools, not reliable execution environments.

---

# Pipeline Execution

Run the pipeline using the configuration file: `python main.py --config config/pipeline_config.yaml`

Example output:
Pipeline execution started
Starting data ingestion
Dataset validation passed
Temporal train-validation split completed
Pipeline execution completed successfully

This execution model prepares the pipeline for integration with:

- Airflow  
- Docker  
- CI/CD pipelines  
- scheduled batch jobs  

---

# Project Structure
```
pharma-demand-forecast/
│
├── config/
│ └── pipeline_config.yaml
│
├── data/
│ └── raw/
│
├── docs/
│ ├── engineering_decisions.md
│ └── data_dictionary.md
│
├── logs/
│
├── notebooks/
│
├── src/
│   ├── ingestion.py
│   ├── validation.py
│   ├── splitting.py
│   ├── processing.py
│   ├── feature_registry.py
│   ├── training.py
│   ├── evaluation.py
│   ├── artifacts.py
│   ├── config_loader.py
│   └── logger.py
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Planned Pipeline Evolution

Next stages of the project include:

- Experiment tracking layer
- Error aggregation by store and calendar patterns
- Feature importance extraction
- Controlled benchmark evolution

---

# Quick Start

Repository:

https://github.com/Luis-Mussalem/pharma-demand-forecast

Clone the repository and run the pipeline:
git clone https://github.com/Luis-Mussalem/pharma-demand-forecast.git

cd pharma-demand-forecast

python main.py --config config/pipeline_config.yaml

---

# Author

Luis Mussalem