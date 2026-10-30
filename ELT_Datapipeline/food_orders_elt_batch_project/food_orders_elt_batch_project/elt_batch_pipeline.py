"""End-to-end batch ELT orchestration."""
import pandas as pd
from load_raw import load_raw
from retrieve_raw import retrieve_raw_batches
from transform import transform_batch
from validate import validate_frame, write_validation_report
from load_transformed import load_transformed_batches
from config import BATCH_SIZE, SOURCE_COLUMNS, REPORT_DIR

def run_pipeline():
    print("=" * 68)
    print("FOOD ORDERS — BATCH ELT PIPELINE")
    print("=" * 68)

    raw_stats = load_raw()

    seen_fingerprints, seen_order_ids = set(), set()
    valid_frames, rejected_frames = [], []
    extracted_from_db = 0
    input_batches = 0
    for input_batches, raw_batch in enumerate(retrieve_raw_batches(), start=1):
        extracted_from_db += len(raw_batch)
        valid, rejected = transform_batch(raw_batch, seen_fingerprints, seen_order_ids)
        if not valid.empty:
            valid_frames.append(valid)
        if not rejected.empty:
            rejected_frames.append(rejected)

    valid_all = pd.concat(valid_frames, ignore_index=True) if valid_frames else pd.DataFrame()
    rejected_all = pd.concat(rejected_frames, ignore_index=True) if rejected_frames else pd.DataFrame()

    # Save rejected rows with clear reasons for audit and reprocessing.
    rejected_path = REPORT_DIR / "rejected_records.csv"
    rejected_all.to_csv(rejected_path, index=False)

    checks = validate_frame(valid_all) if not valid_all.empty else {"non_empty_valid_dataset": False}
    validation_passed = all(checks.values())
    if validation_passed:
        load_stats = load_transformed_batches(valid_frames)
    else:
        # Do not publish data that failed the validation gate.
        load_stats = {
            "analytics_loaded_this_run": 0,
            "analytics_table_count": 0,
            "analytics_successful_batches": 0,
            "analytics_failed_batches": 0
        }

    report = {
        "source_file_records_extracted": raw_stats["raw_loaded"],
        "source_batch_size": BATCH_SIZE,
        "source_batches_processed": (raw_stats["raw_loaded"] + BATCH_SIZE - 1) // BATCH_SIZE,
        "raw_records_loaded_this_run": raw_stats["raw_loaded"],
        "raw_table_total_records": raw_stats["raw_table_count"],
        "raw_records_retrieved": extracted_from_db,
        "retrieval_batches_processed": input_batches,
        "valid_records_transformed": len(valid_all),
        "rejected_records": len(rejected_all),
        "transformed_records_loaded_this_run": load_stats["analytics_loaded_this_run"],
        "analytics_table_total_records": load_stats["analytics_table_count"],
        "successful_batches": raw_stats["raw_successful_batches"] + load_stats["analytics_successful_batches"],
        "failed_batches": raw_stats["raw_failed_batches"] + load_stats["analytics_failed_batches"],
        "validation_checks": checks,
        "final_validation_status": "PASS" if validation_passed else "FAIL",
        "rejected_records_file": str(rejected_path)
    }
    write_validation_report(report)
    print("\nFINAL EXECUTION REPORT")
    for key, value in report.items():
        print(f"{key}: {value}")
    return report

if __name__ == "__main__":
    run_pipeline()
