# Data Dictionary - Rossmann Datase 

## train.csv

## Dataset Overview

- Rows: 1,017,209
- Columns: 9
- Granularity: Store + Date
- Date Range: 2013-01-01 to 2015-07-31
- Null Values: None detected
- Duplicate Records (Store + Date): 0
- Data Consistency Check:
  - Sales = 0 when Open = 0 

## Columns Description

### Store
- Type: Integer
- Description: Unique identifier of each store
- Role: Primary entity key

### DayOfWeek
- Type: Integer (1–7)
- Description: Day of week (1 = Monday, 7 = Sunday)

### Date
- Type: Date
- Description: Daily observation date
- Role: Time index
- Important: Must be converted to datetime format

### Sales
- Type: Float
- Description: Daily sales revenue
- Role: Target variable
- Notes: Zero when store is closed

### Customers
- Type: Integer
- Description: Number of customers that visited the store
- Role: Predictor variable

### Open
- Type: Binary (0/1)
- Description: Indicates if the store was open (1) or closed (0)
- Risk: Sales should be zero when Open = 0

### Promo
- Type: Binary (0/1)
- Description: Indicates whether a promotion was active

### StateHoliday
- Type: Categorical
- Description: Indicates state holiday
- Possible values:
  - 0 = No holiday
  - a = Public holiday
  - b = Easter holiday
  - c = Christmas

### SchoolHoliday
- Type: Binary (0/1)
- Description: Indicates school holiday
