## Data Granularity

The unit of analysis for this project is:

Store + Date

Each row represents the daily sales performance of a specific store.

All transformations must respect this aggregation level.

## Technical Questions

### What is the prediction target?
The prediction target is daily Sales per Store.

### What is the forecasting horizon?
The goal is to predict future daily sales for each store.
Forecast horizon will be defined using temporal split.

### What is the main evaluation metric?
Primary metric: RMSE
Secondary metrics: MAE, MAPE

### What are the risks of data leakage?
- Using future sales values to create lag features
- Random train-test split instead of temporal split
- Using information not available at prediction time