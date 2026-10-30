"""Extract the source CSV without cleaning or modifying its records."""
import pandas as pd
from config import DATA_FILE, BATCH_SIZE, SOURCE_COLUMNS

def extract_batches():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Source CSV was not found: {DATA_FILE}")
    total = 0
    batch_count = 0
    # dtype=str preserves the source representation; blank cells remain blank strings.
    for batch_count, batch in enumerate(
        pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False, chunksize=BATCH_SIZE),
        start=1
    ):
        missing = [c for c in SOURCE_COLUMNS if c not in batch.columns]
        extra = [c for c in batch.columns if c not in SOURCE_COLUMNS]
        if missing or extra:
            raise ValueError(f"Unexpected CSV schema. Missing={missing}; extra={extra}")
        batch = batch[SOURCE_COLUMNS].copy()
        batch.insert(0, "source_row_number",
                     range(total + 1, total + len(batch) + 1))
        total += len(batch)
        print(f"Extract batch {batch_count}: {len(batch)} records")
        yield batch
    print(f"Extraction complete: {total} records in {batch_count} batches")

if __name__ == "__main__":
    sum(len(b) for b in extract_batches())
