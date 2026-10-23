from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient, UpdateOne

from bigdata_project.config import SETTINGS


def get_local_database():
    client = MongoClient(SETTINGS.local_mongo_uri, tls=False)
    return client[SETTINGS.local_mongo_db]


def get_atlas_database():
    if not SETTINGS.atlas_mongo_uri:
        raise ValueError("ATLAS_MONGO_URI is not configured.")
    client = MongoClient(SETTINGS.atlas_mongo_uri, tls=True)
    return client[SETTINGS.atlas_mongo_db]


def ensure_local_indexes(db) -> None:
    db.imported_files.create_index("file_name", unique=True)
    db.import_runs.create_index("run_id", unique=True)


def record_import_status(
    db,
    file_name: str,
    status: str,
    extracted_files: list[str] | None = None,
    details: dict | None = None,
) -> None:
    db.imported_files.update_one(
        {"file_name": file_name},
        {
            "$set": {
                "status": status,
                "extracted_files": extracted_files or [],
                "details": details or {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )


def start_import_run(db, stage: str, details: dict | None = None) -> str:
    run_id = f"{stage}-{uuid.uuid4()}"
    db.import_runs.insert_one(
        {
            "run_id": run_id,
            "stage": stage,
            "status": "running",
            "details": details or {},
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return run_id


def finish_import_run(
    db,
    run_id: str,
    status: str,
    summary: dict | None = None,
) -> None:
    db.import_runs.update_one(
        {"run_id": run_id},
        {
            "$set": {
                "status": status,
                "summary": summary or {},
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


def get_imported_file_status(db, file_name: str) -> str | None:
    document = db.imported_files.find_one({"file_name": file_name}, {"status": 1})
    if not document:
        return None
    return document.get("status")


def insert_cleaned_documents(db, documents: list[dict]) -> None:
    operations = [
        UpdateOne({"_id": document["_id"]}, {"$set": document}, upsert=True)
        for document in documents
    ]
    if operations:
        db.tripdata_cleaned_local.bulk_write(operations, ordered=False)


def create_quality_report(
    db,
    source_file: str,
    input_rows: int,
    output_rows: int,
    report_path: Path | None = None,
) -> None:
    payload = {
        "source_file": source_file,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "dropped_rows": input_rows - output_rows,
        "report_path": str(report_path) if report_path else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.data_quality_reports.update_one(
        {"source_file": source_file},
        {"$set": payload},
        upsert=True,
    )


def write_results_to_atlas(results: list[dict]) -> int:
    db = get_atlas_database()
    collection = db[SETTINGS.atlas_results_collection]
    operations = [
        UpdateOne(
            {"metric": item["metric"], "dimension": item["dimension"]},
            {"$set": item},
            upsert=True,
        )
        for item in results
    ]
    if not operations:
        return 0
    summary = collection.bulk_write(operations, ordered=False)
    return summary.upserted_count + summary.modified_count
