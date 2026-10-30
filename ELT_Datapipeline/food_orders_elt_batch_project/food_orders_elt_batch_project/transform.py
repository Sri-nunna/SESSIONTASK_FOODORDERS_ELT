"""Batch transformations. Duplicate tracking is shared across all batches."""
import hashlib
import json
import pandas as pd
from config import SOURCE_COLUMNS, DATETIME_COLUMNS, FINANCIAL_COLUMNS, CATEGORY_COLUMNS

def row_fingerprint(row):
    values = [None if pd.isna(row.get(c)) else str(row.get(c)) for c in SOURCE_COLUMNS]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode("utf-8")).hexdigest()

def transform_batch(batch, seen_fingerprints, seen_order_ids):
    frame = batch.copy()
    accepted, rejected = [], []

    for _, source_row in frame.iterrows():
        record = source_row.to_dict()
        source_no = int(record["source_row_number"])
        fingerprint = row_fingerprint(record)

        if fingerprint in seen_fingerprints:
            rejected.append({**record, "rejection_reason": "exact_duplicate_row"})
            continue
        seen_fingerprints.add(fingerprint)

        raw_order_id = record.get("Order ID")
        order_id = str(raw_order_id).strip() if raw_order_id is not None else ""
        if order_id and order_id in seen_order_ids:
            rejected.append({**record, "rejection_reason": "repeated_order_id_nonidentical_record"})
            continue
        if order_id:
            seen_order_ids.add(order_id)

        accepted.append(record)

    if not accepted:
        return pd.DataFrame(), pd.DataFrame(rejected)

    df = pd.DataFrame(accepted)
    # Preserve source row number for lineage and convert fields explicitly.
    for col in DATETIME_COLUMNS:
        df[col] = pd.to_datetime(df[col].replace("", pd.NA), errors="coerce")

    for col in FINANCIAL_COLUMNS:
        df[col] = pd.to_numeric(df[col].replace("", pd.NA), errors="coerce")

    # Missing category labels are explicit; no claim is made that an offer was absent.
    for col in CATEGORY_COLUMNS:
        df[col] = df[col].replace("", pd.NA).fillna(
            "Not Specified" if col == "Discounts and Offers" else "Unknown"
        )

    df["Order ID"] = pd.to_numeric(df["Order ID"], errors="coerce").astype("Int64")
    df["Delivery_Time_Minutes"] = (
        df["Delivery Date and Time"] - df["Order Date and Time"]
    ).dt.total_seconds() / 60
    df["Order_Date"] = df["Order Date and Time"].dt.date
    df["Order_Hour"] = df["Order Date and Time"].dt.hour.astype("Int64")

    components = ["Commission Fee", "Delivery Fee",
                  "Payment Processing Fee", "Refunds/Chargebacks"]
    df["Platform_Net_Revenue"] = (
        df["Commission Fee"] + df["Delivery Fee"]
        - df["Payment Processing Fee"] - df["Refunds/Chargebacks"]
    )

    # Invalid/missing timestamps and negative delivery intervals are quarantined.
    invalid_timestamp = df[DATETIME_COLUMNS].isna().any(axis=1)
    negative_duration = df["Delivery_Time_Minutes"].lt(0)
    invalid_mask = invalid_timestamp | negative_duration

    for idx, row in df.loc[invalid_mask].iterrows():
        reasons = []
        if row[DATETIME_COLUMNS].isna().any():
            reasons.append("invalid_or_missing_timestamp")
        if pd.notna(row["Delivery_Time_Minutes"]) and row["Delivery_Time_Minutes"] < 0:
            reasons.append("negative_delivery_duration")
        original = {c: row.get(c) for c in SOURCE_COLUMNS}
        original["source_row_number"] = int(row["source_row_number"])
        rejected.append({**original, "rejection_reason": ";".join(reasons)})

    valid = df.loc[~invalid_mask].copy()
    # Ensure output contains only the columns defined in the analytics table.
    output_columns = ["source_row_number"] + SOURCE_COLUMNS + [
        "Delivery_Time_Minutes", "Order_Date", "Order_Hour", "Platform_Net_Revenue"
    ]
    valid = valid[output_columns]
    return valid, pd.DataFrame(rejected)
