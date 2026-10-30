"""Read raw rows back from MySQL in deterministic batches."""
import pandas as pd
from db_utils import database_connection
from config import RAW_DATABASE, SOURCE_COLUMNS, BATCH_SIZE

def retrieve_raw_batches():
    conn = database_connection(RAW_DATABASE)
    columns = ["source_row_number"] + SOURCE_COLUMNS
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_food_orders")
        total = cur.fetchone()[0]
        offset = 0
        batch_no = 0
        while offset < total:
            cur.execute(
                f"SELECT {', '.join(f'`{c}`' for c in columns)} "
                "FROM raw_food_orders ORDER BY source_row_number LIMIT %s OFFSET %s",
                (BATCH_SIZE, offset)
            )
            rows = cur.fetchall()
            if not rows:
                break
            batch_no += 1
            frame = pd.DataFrame(rows, columns=columns)
            print(f"Retrieve batch {batch_no}: {len(frame)} records")
            yield frame
            offset += len(rows)
        print(f"Retrieval complete: {offset} records in {batch_no} batches")
    finally:
        conn.close()
