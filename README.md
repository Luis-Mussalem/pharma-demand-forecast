# Pharma Demand Forecast — Data Engineering Pipeline

## Project Overview

This project focuses on building a structured and reproducible data engineering pipeline for daily demand forecasting using the Rossmann Store Sales dataset.

The primary goal is not only forecasting performance, but to design a modular architecture that enforces:

- Explicit data contracts
- Schema validation
- Type enforcement
- Granularity control
- Structured logging
- Reproducibility

This project represents a transition from analytical exploration to production-oriented data architecture.

---

## Technical Objectives

- Build a modular pipeline using a `src/` structure
- Enforce strict schema and data type validation
- Prevent data leakage through controlled transformations
- Implement structured logging for observability
- Ensure reproducibility outside notebook environments

---

## Data Granularity

Unit of analysis:

**Store + Date**

Each row represents the daily sales performance of a specific store.

All transformations and validations respect this aggregation level to prevent inconsistencies and data leakage.

---

## Current Implementation Status

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

### ✅ Temporal Train-Validation Split

- Deterministic time-based split implemented in `src/splitting.py`
- Split date controlled via configuration file
- Protection against temporal data leakage
- Logging of train and validation time ranges

---


## Engineering Principles Applied

- Single Responsibility Principle
- Modular project architecture
- Explicit data contracts
- Observability through logging
- Deterministic execution
- Separation between exploration and pipeline logic

---

## Engineering Insights & Challenges

### 1. Dtype Inconsistency (StateHoliday)

Issue:
Pandas raised a DtypeWarning due to mixed types in the `StateHoliday` column.  
Validation failed because the expected dtype did not match the inferred dtype.

Resolution:
- Explicit dtype specification during CSV ingestion.
- Converted `StateHoliday` to categorical type.
- Updated the data contract accordingly.

Lesson:
Data contracts must reflect semantic meaning, not only default technical behavior.

---

### 2. Logging Path Resolution

Issue:
Logs were being generated inside the notebook directory due to relative path resolution.

Resolution:
- Implemented root-path resolution using `__file__`.
- Ensured logs are consistently saved at project root level.

Lesson:
Production systems must not rely on execution context.

---

### 3. Module Reloading in Jupyter

Issue:
Changes to validation modules were not reflected immediately.

Resolution:
- Used `importlib.reload()` during development.
- Reinforced the need for a proper `main.py` entry point.

Lesson:
Notebooks are exploratory tools, not production execution engines.

---

### ✅ Ingestion Layer

- Dedicated `src/ingestion.py` module
- Explicit dtype enforcement during CSV loading
- Deterministic datetime parsing
- Immediate schema validation after load
- CLI-executable via `main.py`
- Fail-fast behavior on invalid input

---

## Pipeline Execution

The project includes a CLI-ready pipeline entry point implemented in `main.py`.

This allows the entire data ingestion and validation workflow to be executed outside notebooks in a deterministic way.

Example execution:

python main.py --data-path data/raw/train.csv

Key characteristics of the entry point:

- CLI interface implemented with `argparse`
- Runtime configuration through command line arguments
- Structured logging during execution
- Automatic dataset validation during ingestion
- Fail-fast behavior when data contracts are violated

This design prepares the pipeline for integration with orchestration systems such as Airflow, Docker, or CI/CD environments.

## Pipeline Architecture

The current pipeline execution flow is:

main.py
   ↓
config_loader.py
   ↓
ingestion.py
   ↓
validation.py
   ↓
splitting.py

Each module has a well-defined responsibility:

- **main.py** — CLI entry point and pipeline orchestration
- **config_loader.py** — external configuration management
- **ingestion.py** — controlled dataset loading
- **validation.py** — data contract enforcement
- **splitting.py** — deterministic temporal train-validation split
- **logger.py** — structured logging system

This layered architecture ensures modularity, observability, and deterministic execution.

---

## Project Structure

```

pharma-demand-forecast/
│
├── config/
│   └── pipeline_config.yaml
│
├── data/
│   ├── raw/
│
├── docs/
│   ├── engineering_decisions.md
│   └── data_dictionary.md
│
├── logs/
│
├── notebooks/
│
├── src/
│   ├── ingestion.py
│   ├── validation.py
│   ├── splitting.py
│   ├── config_loader.py
│   └── logger.py
│
├── main.py
├── requirements.txt
└── README.md

```

---

## Quick Start

Clone the repository and run the pipeline:

git clone https://github.com/<your-user>/pharma-demand-forecast.git
cd pharma-demand-forecast

python main.py --data-path data/raw/train.csv

---

## Next Steps

---

## Author

Luis Mussalem