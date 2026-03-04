# Engineering Decisions — Pharma Demand Forecast

This document details technical decisions, issues encountered, and architectural reasoning throughout the development process.

---
## Days 1 & 2

## 1. Data Contract Implementation

### Decision

Implement explicit schema validation before any transformation.

### Why

Without schema enforcement:
- Silent failures occur downstream.
- Feature engineering may break unexpectedly.
- Debugging becomes significantly harder.

### Implementation

- `EXPECTED_COLUMNS`
- `EXPECTED_DTYPES`
- Granularity validation (Store + Date uniqueness)
- Fail-fast exceptions

---

## 2. Granularity Enforcement

### Definition

The dataset granularity is defined as:

Store + Date

### Risk if ignored

- Incorrect lag calculations
- Invalid rolling window calculations
- Data leakage
- Duplicate training signals

### Mitigation

Implemented duplicate detection: 

df.duplicated(subset=["Store", "Date"])

Pipeline stops if duplicates exist.

---

## 3. StateHoliday Dtype Resolution

### Problem

Pandas raised:

DtypeWarning: mixed types

`StateHoliday` contained both numeric and string values.

### Root Cause

Pandas inferred inconsistent types due to mixed column values.

### Resolution

- Explicit dtype specification in `read_csv`
- Converted column to categorical type
- Updated validation contract

### Engineering Insight

Semantic types matter.
Categorical variables should not be treated as generic objects.

---

## 4. Logging Architecture

### Initial Issue

Logs were saved relative to execution context (notebooks folder).

### Risk

Non-deterministic log storage location.

### Solution

Root-based resolution:

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(file)))

Logs are now consistently stored in: 

project_root/log/pipeline.log

---

## 5. Jupyter Import Behavior

### Issue

Module changes were not reflected after modification.

### Cause

Jupyter caches imported modules.

### Solution

Used:

import importlib
importlib.reload(module)

### Architectural Conclusion

Notebooks are for exploration.
Production execution will occur through a centralized entry point.

---

## 6. Validation Philosophy

Validation is:

- Silent when successful
- Explicit when failing
- Logged structurally
- Designed to fail fast

This prevents downstream corruption and ensures deterministic behavior.

---

## Architectural Direction

The long-term architecture will include:

- Modular ingestion layer
- Controlled transformation pipeline
- Feature engineering isolation
- Time-based splitting
- Modeling abstraction
- Evaluation layer

The current stage establishes the foundation required for reliable machine learning workflows.

## Day 3 — Ingestion Layer Implementation

### Decision
Created a dedicated ingestion module responsible for:
- Explicit dtype control during CSV loading
- Deterministic datetime parsing
- Immediate dataset validation
- Structured logging integration

### Rationale
Separating ingestion from exploration ensures:
- Single Responsibility Principle
- Reproducible execution
- Prevention of schema drift
- Production-ready architecture

### Improvements
- Logger refactored to idempotent configuration
- Robust dtype comparison using is_dtype_equal

## Day 3 — CLI Entry Point Implementation

### Decision

Implemented a CLI-ready `main.py` using `argparse`.

### Why

- Remove dependency on notebook execution
- Enable deterministic pipeline execution
- Prepare project for orchestration tools (Airflow, Docker, CI/CD)
- Allow runtime configuration via command line

### Implementation

- Required argument: `--data-path`
- Optional arguments:
  - `--log-level`
  - `--save-processed`
  - `--output-path`
- Structured error handling with `sys.exit(1)`
- Explicit path resolution using `Path.resolve()`

### Engineering Insight

Production pipelines must not rely on hardcoded paths or execution context.
CLI configuration ensures reproducibility and portability.

## Day 3 — Temporal Train-Validation Split

### Decision

Implement deterministic temporal splitting before feature engineering.

### Why

Random dataset splits introduce temporal leakage in forecasting problems.
Models may learn patterns from the future, producing unrealistic performance.

A strict chronological split prevents this issue.

### Implementation

A dedicated module (`src/splitting.py`) performs:

- explicit ordering by date
- deterministic split based on configuration
- validation checks preventing overlap
- structured logging of split periods

### Configuration

The split date is defined in the pipeline configuration:

split:
  method: date
  split_date: "2015-04-30"

### Engineering Insight

Temporal integrity must be enforced before any feature engineering step,
especially when lag or rolling-window features are introduced.

