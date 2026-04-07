# Pharma Demand Forecast — Modular ML Pipeline & Governance Architecture

![Python](https://img.shields.io/badge/Python-3.12-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-orange)
![Pipeline](https://img.shields.io/badge/Pipeline-Modular-green)
![Architecture](https://img.shields.io/badge/Architecture-MLOps-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## What This Project Is

A production-oriented ML pipeline for daily sales forecasting across 1,115 retail pharmacy stores, built on the [Rossmann Store Sales](https://www.kaggle.com/c/rossmann-store-sales) dataset.

The focus is **not** predictive performance alone — it is the complete engineering system around a model:

- Explicit data contracts with fail-fast validation
- Schema-versioned training and inference pipelines
- Config-driven feature engineering with registry orchestration
- Explainable champion model promotion with threshold-based governance
- Non-blocking inference drift monitoring with baseline alignment
- Governed artifact lifecycle with timestamped persistence and automatic archiving
- Power BI consumption layer with semantic contracts

This project was deliberately designed as a **controlled architecture exercise** to demonstrate real ML pipeline engineering maturity.

---

## What Makes This Different

Most portfolio ML projects are notebooks with `model.fit()`. This repository demonstrates:

| Concern | Implementation |
|---|---|
| **Data contracts** | Schema registry with versioned training and inference contracts |
| **Temporal integrity** | Deterministic split with anti-leakage verification |
| **Feature orchestration** | Config-driven registry — features activated through YAML, not code |
| **Model governance** | Registry-based champion policy with explainable promotion decisions |
| **Promotion explainability** | Every challenger evaluation persists reason code, thresholds, and deltas |
| **Drift monitoring** | Champion-aligned baseline statistics with z-score mean-shift detection |
| **Baseline resolution** | Automatic backfill with explicit resolution source traceability |
| **Governance alerts** | Configurable thresholds for consecutive rejections, critical drift, baseline backfill recurrence |
| **Artifact lifecycle** | Timestamped persistence, archive rotation, champion retention during cleanup |
| **BI consumption** | Flat CSV exports with formal semantic contracts for Power BI |
| **Engineering history** | 22 documented engineering days with decisions, errors, and rationale |

---

## Architecture

```text
                ┌─────────────────────────┐
                │         main.py         │
                │  Training Orchestration  │
                └────────────┬────────────┘
                             │
               ┌─────────────┼──────────────┐
               ▼             ▼              ▼
        ┌────────────┐ ┌──────────┐ ┌──────────────┐
        │ ingestion  │ │ config   │ │ schema       │
        │            │ │ loader   │ │ registry     │
        └─────┬──────┘ └──────────┘ └──────────────┘
              ▼
        ┌────────────┐
        │ validation │
        └─────┬──────┘
              ▼
        ┌────────────┐
        │ splitting  │
        └─────┬──────┘
              ▼
        ┌────────────────┐
        │ feature        │
        │ registry +     │
        │ processing     │
        └─────┬──────────┘
              ▼
        ┌────────────┐
        │ training   │
        └─────┬──────┘
              ▼
        ┌────────────┐     ┌────────────┐
        │ evaluation │────▶│ importance │
        └─────┬──────┘     └────────────┘
              ▼
        ┌────────────────────────────────┐
        │          artifacts             │
        │  persistence · promotion ·     │
        │  archiving · governance ·      │
        │  Power BI exports              │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │       predict.py        │
        │  Inference Orchestration│
        └────────────┬────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
   ┌───────────┐ ┌────────┐ ┌───────┐
   │ inference │ │ drift  │ │ gov   │
   │ validation│ │ detect │ │ alerts│
   └───────────┘ └────────┘ └───────┘
```

Training produces governed artifacts. Inference consumes them. The two pipelines share modules but never share execution.

---

## Pipeline Modules

| Module | Responsibility |
|---|---|
| `src/ingestion.py` | Controlled CSV loading with explicit dtypes and datetime parsing |
| `src/validation.py` | Training schema contract: columns, dtypes, Store+Date granularity |
| `src/inference_validation.py` | Inference schema contract: required columns, nulls, leakage prevention |
| `src/schema_registry.py` | Versioned schema definitions for training and inference |
| `src/splitting.py` | Deterministic temporal split with anti-leakage guard |
| `src/processing.py` | Pure feature transformations: calendar, lag, rolling, promo |
| `src/feature_registry.py` | Config-driven feature orchestration and validation context |
| `src/training.py` | Model factory, data preparation, categorical encoding, fitting |
| `src/evaluation.py` | Validation scoring (MAE, RMSE), prediction generation |
| `src/importance.py` | Permutation-based feature importance |
| `src/inference.py` | Champion loading, historical context reconstruction, inference preparation |
| `src/drift.py` | Distribution baseline computation and z-score drift detection |
| `src/artifacts.py` | Artifact lifecycle, promotion policy, governance summary, alerts, Power BI exports |
| `src/config_loader.py` | YAML configuration loader |
| `src/logger.py` | Structured logging (console + file) |

---

## Governance System

### Champion Promotion

- Promotion decision compares challenger vs champion on configurable metric (default: MAE)
- Requires both absolute and relative improvement thresholds
- Every decision persists: reason code, metric deltas, threshold values
- Reason codes: `NO_CHAMPION_BASELINE`, `PROMOTED_THRESHOLD_MET`, `REJECTED_ABSOLUTE_THRESHOLD`, `REJECTED_RELATIVE_THRESHOLD`, `REJECTED_ABSOLUTE_AND_RELATIVE`

### Drift Monitoring

- Training persists model-input distribution baseline (mean, std, min, max per feature)
- Inference loads champion-aligned baseline and computes z-score mean-shift per feature
- Non-blocking: drift report is persisted but does not halt inference
- Baseline resolution is traceable: exact source (active, archive, backfill) is recorded

### Governance Alerts

Configurable through `pipeline_config.yaml`:
- Consecutive promotion rejection threshold
- Critical drift feature count threshold
- Recurrent baseline backfill threshold

---

## Current Model Baseline

| Metric | Value |
|---|---|
| Model | HistGradientBoostingRegressor |
| MAE | 508.37 |
| RMSE | 779.23 |
| Features | calendar, lag, rolling, promo |
| Training rows | 914,629 |
| Validation rows | 102,580 |

---

## Known Limitations & Deliberate Scope

This project prioritizes **pipeline architecture and governance** over model optimization. The following limitations are documented and deliberate:

- **Customers feature is leakage in prospective forecasting.** A controlled A/B ablation (Day 20) measured +61 MAE degradation without it. The feature is retained as a known trade-off with explicit documentation.
- **No hyperparameter tuning.** The model uses fixed parameters. Tuning was deliberately excluded to keep scope on infrastructure, not modeling.
- **Single temporal split.** Expanding window cross-validation was not implemented. The current split (train ≤ 2015-04-30, validation > 2015-04-30) is deterministic and reproducible.
- **26 identical benchmark runs.** This demonstrates deterministic reproducibility — same data, same model, same result every time.
- **Dataset is Rossmann (German retail pharmacy), not clinical pharma data.** The project name reflects the retail pharmacy domain.

---

## How to Run

**Training pipeline:**
```bash
python main.py --config config/pipeline_config.yaml
```

**Inference pipeline:**
```bash
python predict.py --config config/pipeline_config.yaml
```

**Run all tests:**
```bash
python -m unittest discover -s tests -p "test_model_governance.py" -v
python -m unittest discover -s tests -p "test_promotion_policy.py" -v
python -m unittest discover -s tests -p "test_drift_monitoring.py" -v
```

---

## Engineering Decisions

All architectural decisions across 22 development days are documented in [`docs/engineering_decisions.md`](docs/engineering_decisions.md), including:

- Problem identification and root cause analysis
- Implementation rationale and alternatives considered
- 20 historical errors with architectural lessons and anti-regression rules
- Verification results for each development day

---

## Tech Stack

- Python 3.12
- pandas 3.0
- scikit-learn 1.8
- PyYAML 6.0
- joblib 1.5
- Power BI Desktop (governance dashboard)

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