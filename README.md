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

### ✅ Controlled Data Loading

- Explicit dtype definition for `StateHoliday`
- Conversion of `StateHoliday` to categorical type
- Explicit datetime conversion for `Date`
- `low_memory=False` to avoid mixed-type warnings

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

## Next Steps

- Implement ingestion layer (`src/ingestion.py`)
- Create a reproducible pipeline entry point (`main.py`)
- Add feature engineering layer
- Introduce time-based train-test split
- Prepare modeling architecture

---

## Project Structure
'''
pharma-demand-forecast/
│
├── data/
│ ├── raw/
│ ├── interim/
│ └── processed/
│
├── docs/
│ └── engineering_decisions.md
│
├── logs/
│
├── notebooks/
│
├── src/
│ ├── validation.py
│ ├── logger.py
│ └── ingestion.py (next step)
│
└── README.md
'''
---

## Author

Luis Mussalem