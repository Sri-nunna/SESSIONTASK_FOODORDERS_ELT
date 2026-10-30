"""Bulk-load validated records into the analytics MySQL database."""
from db_utils import create_databases, create_analytics_table, database_connection
from config import ANALYTICS_DATABASE, BATCH_SIZE

ANALYTICS_COLUMNS = [
    "source_row_number", "Order ID", "Customer ID", "Restaurant ID",
    "Order Date and Time", "Delivery Date and Time", "Order Value", "Delivery Fee",
    "Payment Method", "Discounts and Offers", "Commission Fee",
    "Payment Processing Fee", "Refunds/Chargebacks", "Weather Condition",
    "Order Channel", "Delivery_Time_Minutes", "Order_Date", "Order_Hour",
    "Platform_Net_Revenue"
]

def to_sql_value(value):
    import pandas as pd
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value

def load_transformed_batches(valid_frames):
    create_databases()
    create_analytics_table()
    conn = database_connection(ANALYTICS_DATABASE)
    total = success = failed = 0
    sql = (
        f"INSERT INTO cleaned_food_orders "
        f"({', '.join(f'`{c}`' for c in ANALYTICS_COLUMNS)}) "
        f"VALUES ({', '.join(['%s'] * len(ANALYTICS_COLUMNS))})"
    )
    try:
        cur = conn.cursor()
        for frame in valid_frames:
            for start in range(0, len(frame), BATCH_SIZE):
                part = frame.iloc[start:start+BATCH_SIZE]
                rows = [
                    tuple(to_sql_value(row[c]) for c in ANALYTICS_COLUMNS)
                    for _, row in part.iterrows()
                ]
                if not rows:
                    continue
                try:
                    cur.executemany(sql, rows)
                    conn.commit()
                    total += len(rows)
                    success += 1
                    print(f"Analytics load batch {success}: committed {len(rows)} rows")
                except Exception as exc:
                    conn.rollback()
                    failed += 1
                    print(f"ERROR: analytics batch rolled back: {exc}")
                    raise
        cur.execute("SELECT COUNT(*) FROM cleaned_food_orders")
        final_count = cur.fetchone()[0]
        return {"analytics_loaded_this_run": total, "analytics_table_count": final_count,
                "analytics_successful_batches": success, "analytics_failed_batches": failed}
    finally:
        conn.close()
