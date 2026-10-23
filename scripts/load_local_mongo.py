from __future__ import annotations

import argparse

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.manifest import load_manifest, select_entries
from bigdata_project.mongo_ops import (
    create_quality_report,
    ensure_local_indexes,
    ensure_trip_indexes,
    finish_import_run,
    get_imported_file_status,
    get_local_database,
    insert_cleaned_documents,
    record_import_status,
    start_import_run,
)
from bigdata_project.transform import dataframe_to_documents, iter_csv_chunks, normalize_chunk


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load selected staged CSV files into local MongoDB.")
    parser.add_argument("--year", type=int, help="Only process a single year.")
    parser.add_argument("--month", type=int, help="Only process a single month.")
    parser.add_argument("--limit", type=int, help="Only process the first N manifest entries.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = get_local_database()
    ensure_local_indexes(db)
    manifest = load_manifest()
    entries = select_entries(
        manifest["entries"],
        year=args.year,
        month=args.month,
        limit=args.limit,
    )
    run_id = start_import_run(
        db,
        stage="load_local_mongo",
        details={"entry_count": len(entries), "year": args.year, "month": args.month},
    )
    processed_files = 0
    skipped_files = 0
    total_inserted = 0
    total_modified = 0

    try:
        for entry in entries:
            status = get_imported_file_status(db, entry["file_name"])
            if status == "loaded_local_mongo":
                skipped_files += 1
                print(f"Skipping {entry['file_name']} because it was already imported.")
                continue

            csv_dir = (
                SETTINGS.raw_csv_dir
                / str(entry["year"])
                / f"{entry['month']:02d}"
            )
            csv_files = sorted(csv_dir.glob("*.csv"))
            if not csv_files:
                print(f"No CSV files found for {entry['file_name']} in {csv_dir}")
                continue

            total_input_rows = 0
            total_output_rows = 0
            inserted = 0
            modified = 0
            for csv_file in csv_files:
                for chunk in iter_csv_chunks(csv_file):
                    total_input_rows += len(chunk.index)
                    normalized = normalize_chunk(chunk, csv_file.name)
                    total_output_rows += len(normalized.index)
                    counts = insert_cleaned_documents(db, dataframe_to_documents(normalized))
                    inserted += counts["inserted"]
                    modified += counts["modified"]

            record_import_status(
                db,
                file_name=entry["file_name"],
                status="loaded_local_mongo",
                extracted_files=[str(path) for path in csv_files],
                details={
                    "year": entry["year"],
                    "month": entry["month"],
                    "input_rows": total_input_rows,
                    "output_rows": total_output_rows,
                    "inserted": inserted,
                    "modified": modified,
                },
            )
            create_quality_report(
                db,
                source_file=entry["file_name"],
                input_rows=total_input_rows,
                output_rows=total_output_rows,
            )
            processed_files += 1
            total_inserted += inserted
            total_modified += modified
            print(
                f"Loaded {entry['file_name']} into MongoDB "
                f"({total_output_rows}/{total_input_rows} rows kept, "
                f"inserted {inserted}, modified {modified})"
            )
    except Exception:
        finish_import_run(db, run_id, "failed")
        raise

    ensure_trip_indexes(db)
    documents = db.tripdata_cleaned_local.count_documents({})
    print("Documents in collection:", documents)

    finish_import_run(
        db,
        run_id,
        "completed",
        summary={
            "processed_files": processed_files,
            "skipped_files": skipped_files,
            "inserted": total_inserted,
            "modified": total_modified,
            "documents_in_collection": documents,
        },
    )


if __name__ == "__main__":
    main()