"""Load untouched CSV rows into the raw MySQL database in 100-row batches."""
from db_utils import create_databases, create_raw_table, database_connection
from config import RAW_DATABASE, SOURCE_COLUMNS, BATCH_SIZE
from extract import extract_batches

def load_raw():
    create_databases()
    create_raw_table()
    conn = database_connection(RAW_DATABASE)
    total = successful_batches = failed_batches = 0
    columns = ["source_row_number"] + SOURCE_COLUMNS
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO raw_food_orders ({', '.join(f'`{c}`' for c in columns)}) VALUES ({placeholders})"
    try:
        cur = conn.cursor()
        for batch_no, batch in enumerate(extract_batches(), start=1):
            rows = []
            for row in batch.itertuples(index=False, name=None):
                # Convert empty CSV fields to SQL NULL while preserving all non-empty source strings.
                rows.append(tuple(None if v == "" else v for v in row))
            try:
                cur.executemany(sql, rows)
                conn.commit()
                total += len(rows)
                successful_batches += 1
                print(f"Raw load batch {batch_no}: committed {len(rows)} rows")
            except Exception as exc:
                conn.rollback()
                failed_batches += 1
                print(f"ERROR: raw load batch {batch_no} rolled back: {exc}")
                raise
        cur.execute("SELECT COUNT(*) FROM raw_food_orders")
        db_count = cur.fetchone()[0]
        print(f"Raw table total: {db_count}; this run loaded: {total}")
        if db_count < total:
            raise RuntimeError("Raw table count is lower than the rows loaded in this run.")
        return {"raw_loaded": total, "raw_table_count": db_count,
                "raw_successful_batches": successful_batches,
                "raw_failed_batches": failed_batches}
    finally:
        conn.close()

if __name__ == "__main__":
    load_raw()
