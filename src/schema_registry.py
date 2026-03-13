TRAINING_SCHEMA_V1 = {
    "columns": [
        "Store",
        "DayOfWeek",
        "Date",
        "Sales",
        "Customers",
        "Open",
        "Promo",
        "StateHoliday",
        "SchoolHoliday",
    ],
    "dtypes": {
        "Store": "int64",
        "DayOfWeek": "int64",
        "Date": "datetime64[ns]",
        "Sales": "int64",
        "Customers": "int64",
        "Open": "int64",
        "Promo": "int64",
        "StateHoliday": "category",
        "SchoolHoliday": "int64",
    },
}

INFERENCE_SCHEMA_V1 = {
    "columns": [
        "Store",
        "DayOfWeek",
        "Date",
        "Open",
        "Promo",
        "StateHoliday",
        "SchoolHoliday",
    ]
}

TRAINING_SCHEMAS = {
    "v1": TRAINING_SCHEMA_V1,
}