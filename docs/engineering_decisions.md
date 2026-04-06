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
# Day 8 — External Inference Input Separation

## Decision

Separated inference input from training source by creating a dedicated inference dataset path.

## Why

Training data and prediction input must belong to different operational layers.

Using training source directly during inference creates unrealistic execution behavior.

## Implementation

Created:

data/inference/future_data.csv

Configured through:

pipeline_config.yaml

## Engineering Insight

Inference should simulate production input as early as possible, even in local pipelines.

# Day 8 — Historical Context Stabilization for Inference

## Decision

Refined inference context generation to preserve only valid rows after lag and rolling feature construction.

## Why

Initial inference execution generated empty prediction matrices because temporal feature generation invalidated all future rows.

## Implementation

Applied controlled historic tail selection before feature generation and restricted final inference matrix to valid prediction rows.

## Engineering Insight

Temporal inference pipelines require explicit row survival control after feature creation.

# Day 8 — Configuration Hardening

## Decision

Removed remaining inference hardcodes and aligned runtime paths with centralized configuration.

## Why

Inference and training must follow the same configuration contract.

Hardcoded paths create hidden coupling and reduce portability.

## Implementation

Inference input path is now resolved through pipeline configuration.

Historical training reference remains explicit only where required for lag reconstruction.

## Engineering Insight

Configuration centralization should grow only where it improves control, not where it adds unnecessary indirection.

# Day 8 — Internal Redundancy Cleanup

## Decision

Removed small internal redundancies after inference stabilization.

## Why

Once inference became stable, some local structures no longer justified their existence.

## Engineering Insight

Small redundancies accumulate quickly in modular pipelines and should be removed early before architectural growth.

# Day 8 — Surgical Refactor Principle Consolidation

## Decision

Adopt minimal-change refactor policy for all new adjustments.

## Rule

Every correction must:

- modify only necessary lines  
- preserve current architecture  
- avoid artificial helper expansion  
- maintain linear readability  

## Engineering Insight

Pipeline maturity depends not only on adding layers, but on protecting internal clarity.

## Day 9 — Inference Validation Layer

### Decision

Created a dedicated validation module for inference inputs.

### Why

Inference schema checks were previously embedded inside preprocessing logic, which mixed contract enforcement with feature preparation responsibilities.

This made inference harder to reason about and created duplication risk.

### Implementation

Created:

- `src/inference_validation.py`

The module now validates:

- required columns  
- null detection  
- semantic validation of `DayOfWeek`  
- target leakage handling (`Sales`)  

### Engineering Insight

Inference contracts should be enforced explicitly before any feature generation begins.

Training validation and inference validation must evolve independently because their contracts are structurally different.

## Day 10 — Lightweight Schema Governance

### Decision

Introduced explicit schema registry and schema version selection for training and inference contracts.

### Why

Validation contracts had become stable enough to justify formal governance.

Keeping schema definitions embedded directly inside validation modules would make future evolution harder.

### Implementation

Created:

- `src/schema_registry.py`
- `config/schema_version.yaml`

Training and inference validations now read schema identity explicitly.

### Engineering Insight

Schema governance should begin only after contracts become stable.

Premature schema abstraction would add indirection without real value.

---

## Day 10 — Inference Validation Consolidation

### Decision

Removed duplicated inference schema validation logic from orchestration layer.

### Why

A previous local validation function remained inside `inference.py`, duplicating logic already promoted to `inference_validation.py`.

### Implementation

Inference now uses a single validation source:

- `src/inference_validation.py`

### Engineering Insight

Validation ownership must remain unique.

Duplicated contract logic creates hidden divergence risk.

---

## Day 10 — Runtime Stabilization After Schema Refactor

### Decision

Completed full runtime validation after schema governance changes.

### Issues Resolved

- missing inference runtime config
- missing history window config
- known nulls in `Open`

### Implementation

Inference runtime now explicitly uses:

- `data_path`
- `history_window_days`

Known null values in `Open` are filled before validation.

### Engineering Insight

Schema refactors must always end with full runtime validation.

Architecture is only complete after train and inference execute without regression.

## Day 11 — Lightweight Model Governance

### Decision

Introduced explicit champion model governance for inference.

### Why

Inference previously relied on the latest saved artifact implicitly.

This created ambiguity because latest artifact does not necessarily mean promoted model.

### Implementation

Created:

- `config/model_registry.yaml`

Inference now supports two policies:

- `latest`
- explicit model filename

### Engineering Insight

Model selection policy should become explicit before introducing full model registry complexity.

---

## Day 11 — Champion Promotion Lifecycle

### Decision

Training now updates champion model automatically after successful model persistence.

### Why

Once champion selection became explicit, training also needed to own model promotion.

### Implementation

Added champion promotion inside artifact lifecycle.

After model save:

- registry is updated automatically

### Engineering Insight

A prediction system becomes operationally coherent only when training promotes and inference consumes the same governed artifact.

## Day 11 — Closure

### Decision
Formally close Day 11 by recording final status and verification artifacts.

### Implementation
- Champion governance implemented (`config/model_registry.yaml`, `src/artifacts.py`, `src/inference.py`).
- Regression tests added: `tests/test_model_governance.py`.
- Agent contract committed: `AGENTS.md`.
- README status updated to reflect Day 11 completion.

### Verification
- Re-run governance tests:
  `python -m unittest discover -s tests -p "test_model_governance.py" -v`
- Sanity-run main pipeline (smoke): `python main.py --config config/pipeline_config.yaml` (optional in CI).

### Action / Release
- Commit documentation updates.

## Day 12 — Benchmark-Aware Champion Promotion

### Decision

Introduced metric-aware champion promotion policy so training promotes challenger only when improvement thresholds are met.

### Why

Day 11 established explicit champion governance, but promotion was still unconditional.
This could overwrite a valid champion with a weaker challenger.

### Implementation

- Added `promotion_policy` in `config/model_registry.yaml` with:
  - `metric`
  - `direction`
  - `min_relative_improvement`
  - `min_absolute_improvement`
- Added `should_promote()` in `src/artifacts.py` as pure decision function.
- Added `load_champion_metrics()` in `src/artifacts.py` to resolve current champion baseline metrics.
- Updated `archive_previous_artifacts(skip_model=...)` to preserve current champion file during artifact rotation.
- Integrated promotion decision in `main.py`:
  - evaluate challenger metrics
  - compare against champion metrics
  - update champion only when policy returns `True`
- Added regression coverage in `tests/test_promotion_policy.py`:
  - no champion baseline
  - threshold met
  - absolute threshold fail
  - relative threshold fail
  - invalid direction
  - champion metrics loading behavior
- Persisted promotion decision audit in artifacts:
  - `promotion_audit` section in `experiment_summary_*.json`
  - promotion columns in `benchmark_history.csv`
- Added tests for promotion audit persistence in `tests/test_promotion_policy.py`.

### Engineering Insight

Model governance is only meaningful when promotion is explicit, testable, and auditable.
By separating decision logic from orchestration, we preserve ownership boundaries and reduce regression risk.

### Verification
- `python -m unittest discover -s tests -p "test_promotion_policy.py" -v` → `OK`
- `python -m unittest discover -s tests -p "test_model_governance.py" -v` → `OK`

## Day 13 — Explainable Promotion Decision Trace

### Decision

Introduced explainable promotion decisions by persisting reason codes and threshold context for each challenger evaluation.

### Why

Day 12 introduced metric-aware promotion, but decision outcomes still lacked explicit semantic trace for reviewers and future governance analysis.

### Implementation

- Added `evaluate_promotion()` in [src/artifacts.py](src/artifacts.py) returning structured decision payload with:
  - `reason_code`
  - improvement values
  - threshold values
  - promotion result
- Kept `should_promote()` as backward-compatible wrapper over `evaluate_promotion()`.
- Updated [main.py](main.py) to use `evaluate_promotion()` and persist enriched `promotion_audit`.
- Extended benchmark persistence in [src/artifacts.py](src/artifacts.py) with:
  - `promotion_reason_code`
  - `promotion_direction`
  - `absolute_improvement`
  - `relative_improvement`
  - threshold fields
- Expanded regression tests in [tests/test_promotion_policy.py](tests/test_promotion_policy.py) for:
  - reason code branches
  - enriched promotion audit persistence
  - Added `save_promotion_report()` in [src/artifacts.py](src/artifacts.py) to produce `artifacts/promotion_report_latest.json`.
- Wired report generation in [main.py](main.py) after benchmark persistence.
- Added report regression tests in [tests/test_promotion_policy.py](tests/test_promotion_policy.py) covering:
  - benchmark history missing
  - benchmark history empty
  - missing audit columns
  - successful report generation

### Engineering Insight

Promotion governance becomes reviewable only when each decision includes both numeric deltas and semantic reason codes. This reduces ambiguity and improves reproducibility for future challenger policies.

### Verification

- `python -m unittest discover -s tests -p "test_promotion_policy.py" -v` → `OK`
- `python -m unittest discover -s tests -p "test_model_governance.py" -v` → `OK`

## Day 14 — Champion-Aligned Drift Monitoring

### Decision

Introduced a lightweight drift monitoring layer aligned to the active model consumed in inference.

### Why

Day 13 completed explainable promotion governance, but inference still lacked statistical observability over input distribution shifts.
Structural validation alone does not detect silent distribution drift.

### Implementation

- Added drift computation module in src/drift.py:
  - compute_distribution_baseline
  - detect_drift
- Added drift artifact persistence in src/artifacts.py:
  - save_distribution_baseline
  - save_drift_report
  - load_distribution_baseline_for_model
- Extended archive behavior in [artifacts.py](http://_vscodecontentref_/37) to preserve champion-aligned distribution baseline during artifact rotation.
- Updated [main.py](http://_vscodecontentref_/38) to compute model-input baseline from training-ready features and persist distribution_baseline_YYYYMMDD_HHMMSS.json for each run.
- Updated [predict.py](http://_vscodecontentref_/39) to:
  - resolve active model path
  - run inference returning predictions and scored matrix
  - load baseline aligned to active model
  - generate and persist [drift_report_latest.json](http://_vscodecontentref_/40) without blocking inference
- Added runtime drift configuration in config/pipeline_config.yaml:
  - drift.z_score_threshold
- Added dedicated regression suite in tests/test_drift_monitoring.py.
- Hardened promotion report generation in [artifacts.py](http://_vscodecontentref_/41) by handling empty benchmark csv files through EmptyDataError fallback.
- Aligned inference runtime contract in [inference.py](http://_vscodecontentref_/42) to return both result and model input matrix used for scoring.

### Engineering Insight

This step completes a governance triad:
- schema contract validation
- explainable promotion governance
- champion-aligned inference drift observability

Drift remained intentionally non-blocking to preserve runtime continuity while still exposing risk signals as governed artifacts.

### Verification

- python -m unittest discover -s tests -p "test_drift_monitoring.py" -v → OK
- python -m unittest discover -s tests -p "test_model_governance.py" -v → OK
- python -m unittest discover -s tests -p "test_promotion_policy.py" -v → OK
- python [main.py](http://_vscodecontentref_/43) --config [pipeline_config.yaml](http://_vscodecontentref_/44) → completed successfully
- python [predict.py](http://_vscodecontentref_/45) --config [pipeline_config.yaml](http://_vscodecontentref_/46) → completed successfully

### Closure Note

Day 14 closed with champion-aligned drift baseline persistence and non-blocking inference drift report generation.
Suggested tag: day14-drift-monitoring-complete

## Day 15 — Unified Governance Observability Snapshot

### Decision

Introduced a unified governance observability snapshot to consolidate promotion and drift runtime signals into a single governed artifact.

### Why

By Day 14, governance artifacts existed but operational consumption remained fragmented across multiple files.
Reviewers needed to manually reconcile champion registry, promotion decision trace, drift status, and benchmark context.

This slowed observability and reduced clarity for downstream dashboard consumption.

### Implementation

- Added `save_governance_summary()` in `src/artifacts.py` to persist:
  - champion model and champion metrics (when available)
  - promotion report status and latest decision
  - drift report status and drift summary
  - latest benchmark row snapshot
  - consistency checks between registry, promotion, and drift model alignment
- Wired snapshot generation in `main.py` after training artifact persistence.
- Wired snapshot generation in `predict.py` after drift report persistence.
- Added regression coverage in `tests/test_promotion_policy.py`:
  - unified summary happy-path generation
  - resilient behavior when promotion/drift reports are missing
- Fixed inference integration contract mismatch:
  - removed unsupported `timestamp` argument from `save_governance_summary()` call in `predict.py`

### Engineering Insight

This step converts governance from isolated artifacts into a single operationally consumable state.

It improves:
- architectural readability for reviewers
- portability to dashboard and cloud-oriented monitoring flows
- contract stability for future observability evolution (e.g., store-level segmentation)

### Verification

- `python -m unittest discover -s tests -p "test_promotion_policy.py" -v` → `OK`
- `python -m unittest discover -s tests -p "test_drift_monitoring.py" -v` → `OK`
- `python -m unittest discover -s tests -p "test_model_governance.py" -v` → `OK`
- `python main.py --config config/pipeline_config.yaml` → completed successfully
- `python predict.py --config config/pipeline_config.yaml` → completed successfully

### Remaining TODOs / Next Step

- Consume `governance_summary_latest.json` in a dashboard-oriented observability layer.
- Evaluate first segmentation cut (store-level or feature-family-level drift visibility).

### Closure Note

Day 15 closed with unified governance observability snapshot persistence and cross-layer contract alignment after inference integration fix.
Suggested tag: day15-governance-observability-snapshot

## Day 16 — Governance Alerts Parameterization and Panel Snapshot Consolidation

### Decision

Completed governance observability maturation by:
- consolidating dashboard-friendly governance panel snapshot usage
- parameterizing governance alert sensitivity through runtime config
- expanding regression coverage for configurable alert thresholds

### Why

After Day 15, governance observability existed, but alert sensitivity still depended on default runtime parameters and panel-oriented consumption needed explicit closure as an operational contract.

Day 16 focused on turning observability into a tunable governance layer without changing core business rules.

### Implementation

- Confirmed unified panel snapshot persistence:
  - artifacts/governance_panel_latest.json
- Externalized governance alert sensitivity to configuration:
  - governance.alerts.consecutive_rejection_threshold
  - governance.alerts.critical_drift_feature_threshold
- Wired config-driven thresholds into runtime orchestrators:
  - main.py
  - predict.py
- Expanded regression coverage in tests/test_promotion_policy.py:
  - custom threshold path for consecutive rejection alert
  - governance panel snapshot generation

### Engineering Insight

This step separates policy tuning from code logic.
Operational teams can now adjust alert sensitivity via configuration, preserving ownership boundaries and reducing runtime change risk.

### Verification

- python -m unittest discover -s tests -p "test_promotion_policy.py" -v → OK
- python -m unittest discover -s tests -p "test_drift_monitoring.py" -v → OK
- python -m unittest discover -s tests -p "test_model_governance.py" -v → OK
- python main.py --config config/pipeline_config.yaml → completed successfully
- python predict.py --config config/pipeline_config.yaml → completed successfully

### Remaining TODOs / Next Step

- Publish governance panel fields to Power BI semantic model.
- Start segmented governance visibility:
  - store-level drift segmentation
  - feature-family alert rollups

### Closure Note

Day 16 closed with configurable governance thresholds and panel-oriented observability consolidation.
Suggested tag: day16-governance-thresholds-and-panel-ready

---

## Day 17 — Power BI Flat Export and Semantic Contract

### What

Completed the governance observability consumption layer by:
- implementing flat CSV export from governance panel for Power BI direct consumption
- defining explicit semantic contract for Power BI field mapping and refresh semantics

### Why

After Day 16, governance_panel_latest.json provided unified snapshot data, but its nested JSON structure required manual Power BI transformation without a governed contract.

Day 17 established the consumption layer: a flat, single-row CSV contract that Power BI can ingest directly without transformation logic.

### Implementation

- Added save_powerbi_export() to src/artifacts.py:
  - reads governance_panel_latest.json
  - flattens all nested fields into a single-row CSV
  - persists to artifacts/powerbi_export_latest.csv
- Wired save_powerbi_export into training pipeline: main.py
- Wired save_powerbi_export into inference pipeline: predict.py
- Created semantic contract document: powerbi/governance_panel_contract.md
  - 19-field schema contract with types, nullability, semantic rules
  - recommended Power BI model mapping
  - data quality checks for refresh validation

### Engineering Insight

The flat CSV export separates the internal pipeline governance representation (nested JSON) from the analytical consumption contract (tabular CSV). This prevents BI layer from depending on internal JSON schema evolution and makes the refresh contract explicit and stable.

### Verification

- python -m unittest discover -s tests -p "test_promotion_policy.py" -v → 30 tests OK (including TestPowerBIExport)
- python -m unittest discover -s tests -p "test_model_governance.py" -v → 4 tests OK
- python -m unittest discover -s tests -p "test_drift_monitoring.py" -v → 8 tests OK
- python main.py --config config/pipeline_config.yaml → completed successfully
- python predict.py --config config/pipeline_config.yaml → completed successfully
- artifacts/powerbi_export_latest.csv generated with 19 columns and 1 row

### Remaining TODOs / Next Step

- Connect Power BI Desktop to artifacts/powerbi_export_latest.csv
- Build governance dashboard visuals:
  - champion MAE trend
  - promotion status card
  - alerts severity indicator
  - drift status card

### Closure Note

Day 17 closed with flat export contract and Power BI semantic document ready for dashboard connection.
Suggested tag: day17-powerbi-export-contract-ready

---

## Day 18 — Benchmark History Power BI Export Hardening

### What

Completed observability trend consumption by:
- adding stable benchmark history Power BI export typing
- adding analytical datetime field for trend visuals
- defining benchmark history semantic contract for BI

### Why

After Day 17, Power BI snapshot consumption was governed, but trend consumption still depended on a technical export without a dedicated semantic contract and with potential BI typing ambiguity.

Day 18 stabilized benchmark export semantics for direct dashboard trend usage.

### Implementation

- Hardened benchmark export in src/artifacts.py:
  - added run_datetime parsed from timestamp
  - normalized promoted to stable boolean behavior
  - kept benchmark export ownership in artifacts layer
- Extended regression coverage in tests/test_promotion_policy.py:
  - run_datetime expectation
  - promoted default behavior for historical non-audited runs
- Created benchmark contract in powerbi/benchmark_history_contract.md:
  - schema, semantic rules, BI mapping, and refresh data quality checks

### Engineering Insight

This step closes the observability cycle with two governed BI surfaces:
- snapshot state contract (governance panel)
- historical trend contract (benchmark history)

This reduces Power BI-side transformation logic and enforces stable analytical semantics at the producer boundary.

### Verification

- python -m unittest discover -s tests -p "test_promotion_policy.py" -v → 34 tests OK
- python main.py --config config/pipeline_config.yaml → completed successfully
- artifacts/powerbi_benchmark_export_latest.csv regenerated with run_datetime and stable promoted semantics
- grep -n "run_datetime\|promoted\|BenchmarkHistory" powerbi/benchmark_history_contract.md → expected anchors found

### Remaining TODOs / Next Step

- Build Power BI visuals using:
  - artifacts/powerbi_export_latest.csv for latest governance status
  - artifacts/powerbi_benchmark_export_latest.csv for performance trend and promotion timeline
- Start dashboard layout and KPI cards for observability panel

### Closure Note

Day 18 documentation closed with benchmark trend contract and stable BI-ready historical export.
Suggested tag: day18-observability-trend-contract-ready

---

## Day 19 — Power BI Governance Dashboard Construction and Debugging

### What

Built the Power BI governance observability dashboard using the two governed artifacts:
- artifacts/powerbi_export_latest.csv → GovernancePanelLatest table
- artifacts/powerbi_benchmark_export_latest.csv → BenchmarkHistory table

Resolved five classes of Power BI import and DAX errors before functional KPI cards were established.

### Why

Day 18 produced stable, governed CSV artifacts with semantic contracts. Day 19 connects those artifacts to an interactive observability surface that makes pipeline governance visible without inspecting raw files.

### Debugging Work — Power BI Layer

Five non-trivial errors were encountered and resolved during dashboard construction:

**1. pt-BR locale numeric corruption**
mae and rmse values imported as scientific notation (5.08E+15) due to Power BI treating the English decimal point as a thousands separator on pt-BR locale machines. Fixed by rebuilding the Power Query query from scratch in Advanced Editor with explicit Table.TransformColumnTypes(..., "en-US") locale declaration.

**2. type logical silent row exclusion**
Casting promoted to type logical in Power Query caused all 26 rows to be silently excluded from the DAX model during load — preview showed correct data, DAX returned BLANK. Fixed by keeping promoted as type text and using LOWER() string comparison in DAX.

**3. COUNTROWS of empty filtered set returns BLANK**
CALCULATE(COUNTROWS(...), filter) returns BLANK (not 0) when the filter matches zero rows. DIVIDE(BLANK, N, 0) propagates BLANK because the alternate result only activates on zero denominator — not BLANK numerator. Fixed by using SUMX(..., IF(..., 1, 0)) which always returns a numeric value.

**4. Multiple DAX measures in single formula editor**
Pasting multiple Measure = ... definitions into one measure's formula bar caused syntax errors. Each measure must be edited individually.

**5. ALL() wrapper required for context-independent measures**
COUNTROWS(BenchmarkHistory) returned BLANK in Card visuals due to residual filter context. Fixed with COUNTROWS(ALL(BenchmarkHistory)).

### Implementation

- Power Query: two queries (GovernancePanelLatest, BenchmarkHistory) with locale-safe numeric import
Verified Output:
Champion MAE = 508,37 ✓
Champion RMSE = 779,23 ✓
Rows Benchmark = 26 ✓
Audited Rows = 26 ✓
Promoted Rows = 0 ✓
Rejection Count = 26 ✓
Promotion Rate % = 0,00% ✓
Latest Drift Status = baseline_missing ✓
Latest Promotion Status = ok ✓
Champion Model = model_20260316_1... ✓
All trend charts displaying 26 data points ✓
Audit Log table with full benchmark history ✓

### Engineering Insight

The Power BI layer exposed three independent failure modes (locale, type system, DAX evaluation semantics) that are invisible in the Python pipeline. This confirms that the BI consumption layer requires its own validation discipline — semantic contracts alone are insufficient without verifying that numeric types, boolean representations, and DAX evaluation context behave as expected end-to-end.

### Remaining Work

- Build Line chart visuals: MAE trend and RMSE trend by run_datetime
- Build remaining KPI cards from GovernancePanelLatest (alerts, drift status, promotion status, champion model)
- Format measures (Promotion Rate % as percentage, MAE/RMSE with 2 decimal places)

### Closure Note

Day 19 closed. Power BI governance dashboard complete with 4-level layout: executive snapshot, operational governance, trend charts, and benchmark audit log. Five Power BI-specific error classes resolved and documented in AGENTS.md Section 3 (Historical Errors 14–18).

Day 20 — Customers Leakage Assessment and Governance Decision
Decision
Executed a controlled A/B ablation to evaluate whether removing Customers improves production realism without unacceptable performance regression.

Why
By Day 19, the pipeline was architecturally complete, but Customers remained a potential leakage risk for prospective forecasting use-cases.

Before changing production contracts, we needed evidence-based validation of impact on MAE and RMSE.

Implementation
Kept production pipeline unchanged.
Ran controlled experiment with identical split, features, and model:
Scenario A: with Customers
Scenario B: without Customers
Compared performance deltas directly on validation set.
Verified Output (A/B Experiment)
A_with_customers_MAE: 508.367764
A_with_customers_RMSE: 779.234028
B_without_customers_MAE: 569.901549
B_without_customers_RMSE: 879.770080
Delta_MAE_B_minus_A: +61.533785
Delta_RMSE_B_minus_A: +100.536052
Technical Conclusion
Removing Customers at this stage causes severe degradation in both central error (MAE) and tail error (RMSE).

Decision for Day 20:

Keep Customers in the current production baseline.
Do not remove feature without a replacement strategy.
Treat this as a governed trade-off between realism and predictive stability.
Architectural Insight
This step improved governance quality by making model-policy decisions evidence-driven instead of assumption-driven.

What became more robust:

Feature removal now requires measured impact and explicit acceptance criteria.
What duplication was removed:

Eliminated implicit reasoning split between leakage concern and performance concern by unifying both in one A/B decision gate.
What future capability became possible:

Enables next iteration focused on leakage-safe proxy design (for example, historical customer signal) before revisiting feature removal.
Verification
Commands executed successfully:

python -m unittest discover -s tests -p "test_model_governance.py" -v
python -m unittest discover -s tests -p "test_promotion_policy.py" -v
python -m unittest discover -s tests -p "test_drift_monitoring.py" -v
python main.py --config pipeline_config.yaml
python predict.py --config pipeline_config.yaml
python - <<'PY' ... A/B ablation script ... PY
All test suites returned OK and both train/inference pipelines completed successfully.

Remaining TODOs / Next Step
Design and test a leakage-safe replacement for Customers.
Re-run A/B with replacement feature set.
Re-evaluate promotion policy eligibility after replacement experiment.
Closure Note
Day 20 closed with controlled leakage assessment and explicit governance decision: keep Customers temporarily due to measured performance regression after ablation.