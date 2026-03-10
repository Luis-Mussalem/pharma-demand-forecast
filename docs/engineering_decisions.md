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

## Day 3 — Feature Engineering Pipeline

### Decision

Implemented a dedicated feature engineering module (`src/processing.py`) responsible for generating model-ready features.

### Rationale

Feature engineering should be isolated from ingestion and validation layers to maintain clear responsibilities and improve pipeline maintainability.

Separating feature transformations allows:

- easier experimentation
- controlled addition of new features
- better testing of transformations
- prevention of unintended data leakage

### Implementation

The feature engineering module includes:

- `create_calendar_features`
- `create_lag_features`
- `create_rolling_features`
- `run_feature_pipeline`

All transformations are orchestrated through a centralized feature pipeline.

### Features Implemented

Calendar Features

- year
- month
- day
- week_of_year

Lag Features

- `lag_sales_1`
- `lag_sales_7`

Rolling Window Features

- `rolling_mean_sales_7`
- `rolling_mean_sales_14`
- `rolling_std_sales_7`

### Engineering Insight

Lag and rolling features must be computed with strict temporal ordering and correct grouping by store to avoid mixing signals across entities.

All lag calculations are performed using: groupby("Store").shift()
ensuring that each store's historical signal remains isolated.

---

## Day 3 — Leakage-Safe Validation Feature Generation

### Problem

After performing a temporal train-validation split, the first observations in the validation set lack historical context required to compute lag and rolling features.

Example:

Train ends at: 2015-04-30
Validation begins at: 2015-05-01
To compute: lag_sales_1 

for the first validation day, the pipeline requires the previous day’s sales from the training set.

### Solution

A new function was implemented: generate_validation_features() 
This function:

1. Retrieves the last observations of each store from the training dataset.
2. Concatenates this historical context with the validation dataset.
3. Runs the feature engineering pipeline.
4. Removes the historical rows afterward.

### Result

This guarantees:

- correct lag computation
- consistent rolling window statistics
- no temporal leakage
- production-grade feature generation

### Engineering Insight

Forecasting pipelines must preserve **temporal context across dataset boundaries**.

Naively generating features on the validation set alone results in incomplete historical signals and inconsistent model inputs.

## Day 4 — Training Layer

### Decision

Implemented a dedicated training module (`src/training.py`) to isolate model preparation and baseline fitting from feature engineering.

### Rationale

Model training should remain independent from feature generation to preserve modularity and enable future model replacement without affecting upstream transformations.

### Implementation

The training layer includes:

- `prepare_training_data`
- `prepare_features`
- `encode_categorical_features`
- `train_model`

### Engineering Decisions

#### Missing Values

Rows containing missing values generated by lag and rolling features are removed before training.

This ensures model compatibility while preserving deterministic preprocessing.

#### Categorical Encoding

Categorical variables are encoded immediately before model fitting.

This keeps raw engineered features semantically intact until the training stage.

#### Baseline Model

A `RandomForestRegressor` baseline was chosen because:

- robust for tabular data
- minimal preprocessing required
- stable first benchmark

### Engineering Insight

Separating model preparation from feature generation mirrors production ML pipelines, where feature stores and model training layers evolve independently.

## Day 4 — Evaluation Layer

### Decision

Implemented a dedicated evaluation module (`src/evaluation.py`) to measure baseline model performance on the temporal validation set.

### Rationale

Training alone is insufficient in a forecasting pipeline.

A dedicated evaluation layer ensures:

- reproducible validation metrics
- explicit baseline tracking
- comparability across future models

### Implementation

The evaluation module includes:

- validation data preparation
- feature extraction
- categorical encoding
- prediction generation
- metric calculation

### Metrics Used

#### MAE (Mean Absolute Error)

Measures average absolute forecasting error.

#### RMSE (Root Mean Squared Error)

Penalizes larger forecasting errors more heavily.

### Baseline Result

- MAE: 460.82
- RMSE: 714.98

### Engineering Insight

Validation preprocessing must mirror training preprocessing exactly.

Any mismatch between train and validation transformations invalidates metric interpretation.

For this reason, the evaluation module reuses:

- `prepare_training_data`
- `prepare_features`
- `encode_categorical_features`

from the training layer.

## Day 4 — Artifact Persistence Layer

### Decision

Implemented a dedicated artifact persistence module (`src/artifacts.py`) to store model and evaluation outputs.

### Rationale

Pipeline outputs must persist beyond runtime execution.

Saving artifacts ensures:

- reproducibility
- experiment traceability
- future deployment readiness

### Artifacts Generated

- `model.pkl`
- `metrics.json`

### Engineering Insight

Separating artifact persistence from training logic preserves modularity and supports future integration with experiment tracking systems.

### Model Artifact Optimization

The initial baseline model generated an excessively large artifact (~6 GB), which was operationally impractical.

To improve persistence efficiency, tree complexity was constrained using:

- `max_depth=12`
- `min_samples_leaf=20`

This reduced artifact size to ~6 MB while preserving baseline reproducibility.

## Day 5 — Feature Registry Layer

### Decision

Introduced a dedicated feature orchestration layer (`src/feature_registry.py`) to control feature activation externally through configuration.

### Rationale

Feature generation was previously hardcoded inside `processing.py`, which limited experimentation and tightly coupled feature logic with execution flow.

A registry-based approach allows:

- controlled feature activation  
- reproducible ablation studies  
- independent evolution of feature families  

### Implementation

A centralized registry was created:

- `FEATURE_REGISTRY`

Features are now activated through YAML configuration:

    features:
      calendar: true
      lag: true
      rolling: true

### Engineering Insight

Feature generation and feature orchestration must remain separate responsibilities.

`processing.py` now contains only pure feature transformations, while `feature_registry.py` governs execution order.

---

## Day 5 — Feature Lineage in Metrics

### Decision

Extended metrics artifacts to include the list of active features used in each experiment.

### Rationale

Performance metrics without experimental context lose analytical value over time.

### Implementation

Metrics now persist:

- MAE  
- RMSE  
- features_used  

### Engineering Insight

Experiment outputs must preserve the exact feature configuration that generated them.

---

## Day 5 — Artifact Versioning

### Decision

Implemented timestamp-based artifact versioning.

### Rationale

Static artifact names overwrite previous experiments and destroy traceability.

### Implementation

Artifacts now persist with execution timestamp:

- model_YYYYMMDD_HHMMSS.pkl  
- metrics_YYYYMMDD_HHMMSS.json  

### Engineering Insight

Artifacts should be immutable outputs of each pipeline execution.

---

## Day 5 — Prediction Persistence Layer

### Decision

Added validation prediction persistence.

### Rationale

Metrics alone are insufficient for model diagnostics.

### Implementation

A dedicated artifact now stores:

- Store  
- Date  
- actual_sales  
- predicted_sales  
- absolute_error  

### Artifact Generated

- predictions_YYYYMMDD_HHMMSS.csv  

### Engineering Insight

Persisted predictions enable direct diagnostic analysis without re-running inference.

---

## Day 5 — Error Analysis Layer

### Decision

Added automatic persistence of top prediction errors.

### Rationale

The pipeline should surface where the model fails most severely.

### Implementation

Top-N largest absolute errors are saved automatically:

- top_errors_YYYYMMDD_HHMMSS.csv  

### Engineering Insight

Error persistence transforms evaluation from scalar metrics into actionable model diagnosis.

## Day 6 — Model Comparison Layer

### Decision

Introduced a controlled model factory inside `src/training.py` to support multiple algorithms without changing pipeline orchestration.

### Rationale

The training layer previously contained a single hardcoded model, which limited experimentation and created architectural coupling.

A model factory allows:

- external model selection  
- reproducible experiment comparison  
- future algorithm expansion  

### Implementation

A new function was introduced:

- `build_model(model_name)`

Supported models:

- `RandomForestRegressor`
- `HistGradientBoostingRegressor`

Model selection is now controlled through YAML:

    model:
      name: hist_gradient_boosting

### Engineering Insight

Model construction and model fitting must remain separate responsibilities.

`build_model()` now handles model creation, while `train_model()` handles data preparation and fitting.

This introduces the first layer of experiment architecture.

---

## Day 6 — Model Lineage in Metrics

### Decision

Extended metrics artifacts to include model identity.

### Rationale

Multiple models require explicit experiment lineage.

### Implementation

Metrics now persist:

- model  
- MAE  
- RMSE  
- features_used  

### Engineering Insight

Metrics without model identity become analytically incomplete in multi-model environments.

---

## Day 6 — Baseline Comparison Result

### Experimental Result

#### RandomForestRegressor

- MAE: 513.96  
- RMSE: 802.35  

#### HistGradientBoostingRegressor

- MAE: 508.37  
- RMSE: 779.23  

### Interpretation

HistGradientBoosting improved both average error and large-error behavior.

The stronger reduction in RMSE indicates better handling of extreme forecasting errors.

### Error Analysis Insight

Top prediction errors remain concentrated in a small set of stores, especially Store 909.

This indicates that model improvement alone is not sufficient to fully capture extreme sales spikes.

The remaining limitation is likely related to feature expressiveness rather than model capacity.

### Engineering Insight

At the current feature maturity level, boosting benefits more from lag and rolling features than bagging.

The experiment also confirmed that extreme forecasting errors now represent the main opportunity for future pipeline evolution.

## Day 6 — Error Aggregation Layer

### Decision

Added store-level error aggregation as a diagnostic artifact.

### Rationale

Global metrics hide local instability.

A forecasting pipeline must identify where performance degrades systematically.

### Implementation

A dedicated artifact now persists:

- mean absolute error by store  
- max absolute error by store  
- number of observations  

Artifact generated:

- error_by_store_YYYYMMDD_HHMMSS.csv

### Engineering Insight

Forecast diagnostics should not stop at global MAE and RMSE.

Store-level aggregation exposes structural model weaknesses that metrics alone cannot reveal.

---

## Day 6 — Feature Importance Layer

### Decision

Introduced permutation-based feature importance after evaluation.

### Rationale

Model metrics quantify performance but do not explain feature contribution.

A production-oriented ML pipeline should expose signal hierarchy.

### Implementation

A dedicated artifact now persists:

- feature  
- importance_mean  
- importance_std  

Artifact generated:

- feature_importance_YYYYMMDD_HHMMSS.csv

### Main Observation

Current strongest predictors:

- Customers  
- Promo  
- rolling_mean_sales_14  
- lag_sales_1  

### Engineering Insight

Feature importance revealed that demand remains strongly dependent on customer volume and recent temporal memory.

---

## Day 6 — Benchmark History Layer

### Decision

Added cumulative benchmark persistence across executions.

### Rationale

Metrics isolated by execution do not support longitudinal experiment tracking.

### Implementation

A cumulative artifact now persists:

- timestamp  
- model  
- MAE  
- RMSE  
- features_used  

Artifact:

- benchmark_history.csv

### Engineering Insight

Even lightweight benchmark tracking significantly improves experimental governance before adopting external tracking systems.

---

## Day 6 — Automatic Artifact Archiving

### Decision

Implemented automatic archiving of previous artifacts before new persistence.

### Rationale

Repeated execution generated artifact accumulation inside the active output folder.

This reduced readability and operational clarity.

### Implementation

A housekeeping function now moves previous outputs into:

- archive/models  
- archive/metrics  
- archive/predictions  
- archive/diagnostics  

while preserving:

- benchmark_history.csv

### Engineering Insight

Artifact lifecycle management is part of production pipeline architecture.

Persistence without retention policy eventually degrades operational quality.

## Day 7 — Inference Layer

### Decision

Created a dedicated inference pipeline separated from training execution.

### Rationale

Training and inference must not share the same execution entry point.

A production pipeline requires isolated prediction flow using persisted model artifacts.

### Implementation

A new entry point was introduced:

- `predict.py`

The inference flow now performs:

- configuration loading  
- raw data ingestion  
- validation  
- feature generation  
- latest model discovery  
- model loading  
- prediction generation  

### Engineering Insight

Separating inference from training is a core production architecture principle.

The training pipeline produces artifacts.

The inference pipeline consumes artifacts.

---

## Day 7 — Champion Model Loading

### Decision

Implemented automatic loading of the latest available model artifact.

### Rationale

Inference should not depend on manually defined model paths.

### Implementation

The pipeline now automatically selects:

- latest `model_YYYYMMDD_HHMMSS.pkl`

from:

- `artifacts/`

### Engineering Insight

This establishes the first lightweight champion model mechanism.

---

## Day 7 — Inference Schema Hardening

### Decision

Added schema sanitization before prediction.

### Rationale

Inference inputs may contain columns not required by the model.

The target column must never enter prediction flow.

### Implementation

When detected:

- `Sales` is automatically removed

A log is emitted:

- Sales column detected in inference input and removed

### Engineering Insight

Inference pipelines must actively sanitize input schemas before scoring.

---

## Day 7 — Inference Artifact Persistence

### Decision

Added persistence for inference outputs.

### Rationale

Inference results should be reproducible and auditable.

### Implementation

A dedicated artifact now persists:

- inference_predictions_YYYYMMDD_HHMMSS.csv

### Engineering Insight

Prediction persistence closes the first full training → artifact → inference cycle.

## Day 7 — Inference Artifact Retention

### Decision

Separated inference artifact archiving from training artifact archiving.

### Rationale

Inference outputs must not trigger movement of training artifacts.

Training and inference require independent retention policies.

### Implementation

A dedicated function was introduced:

- archive_inference_artifacts()

This function archives only:

- inference_predictions_*.csv

into:

- archive/predictions

### Engineering Insight

Artifact lifecycle policies must follow execution responsibility.

Training artifacts and inference artifacts belong to different operational flows.

---

## Day 7 — Inference Schema Validation

### Decision

Promoted inference schema checks to an explicit validation function.

### Rationale

Schema validation should not remain hidden inside preprocessing logic.

### Implementation

A dedicated function now validates:

- required columns  
- missing columns  
- target leakage (`Sales`)  

before feature preparation.

### Engineering Insight

Validation must appear explicitly before transformation in production pipelines.