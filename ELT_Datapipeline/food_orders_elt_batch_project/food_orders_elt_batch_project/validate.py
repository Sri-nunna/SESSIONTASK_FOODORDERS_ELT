"""Validation checks and machine-readable pipeline report generation."""
import json
import pandas as pd
from config import REPORT_DIR, SOURCE_COLUMNS

EXPECTED = ["source_row_number"] + SOURCE_COLUMNS + [
    "Delivery_Time_Minutes", "Order_Date", "Order_Hour", "Platform_Net_Revenue"
]

def validate_frame(df):
    checks = {
        "expected_columns_present": all(c in df.columns for c in EXPECTED),
        "no_full_duplicate_rows": not df.duplicated(subset=SOURCE_COLUMNS).any(),
        "no_negative_delivery_durations": not df["Delivery_Time_Minutes"].dropna().lt(0).any(),
        "datetime_columns_are_datetime": all(
            pd.api.types.is_datetime64_any_dtype(df[c]) for c in
            ["Order Date and Time", "Delivery Date and Time"]
        ),
        "financial_columns_are_numeric": all(
            pd.api.types.is_numeric_dtype(df[c]) for c in
            ["Order Value", "Delivery Fee", "Commission Fee",
             "Payment Processing Fee", "Refunds/Chargebacks", "Platform_Net_Revenue"]
        ),
        "revenue_only_when_all_components_present": (
            df.loc[df[["Commission Fee", "Delivery Fee", "Payment Processing Fee",
                       "Refunds/Chargebacks"]].notna().all(axis=1),
                   "Platform_Net_Revenue"].notna().all()
        ),
        "delivery_duration_calculation_correct": (
            (df["Delivery_Time_Minutes"] -
             (df["Delivery Date and Time"] - df["Order Date and Time"]).dt.total_seconds() / 60)
            .abs().fillna(0).lt(1e-9).all()
        ),
        "revenue_formula_calculation_correct": (
            (df["Platform_Net_Revenue"] -
             (df["Commission Fee"] + df["Delivery Fee"] -
              df["Payment Processing Fee"] - df["Refunds/Chargebacks"]))
            .abs().fillna(0).lt(1e-9).all()
        ),
        "unique_order_ids_in_accepted_records": not df["Order ID"].dropna().duplicated().any()
    }
    return {key: bool(value) for key, value in checks.items()}

def write_validation_report(report):
    path = REPORT_DIR / "validation_report.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, default=str)
    print(f"Validation report saved: {path}")
    return path
