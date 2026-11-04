from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_root: Path
    manifest_dir: Path
    raw_zip_dir: Path
    raw_csv_dir: Path
    processed_dir: Path
    outputs_dir: Path
    docs_dir: Path
    manifest_name: str
    years: tuple[int, ...]
    local_mongo_uri: str
    local_mongo_db: str
    atlas_mongo_uri: str
    atlas_mongo_db: str
    atlas_results_collection: str
    webhdfs_url: str
    hdfs_user: str
    hdfs_raw_dir: str
    hdfs_processed_dir: str


def _parse_years(raw_value: str) -> tuple[int, ...]:
    years = tuple(int(part.strip()) for part in raw_value.split(",") if part.strip())
    if not years:
        raise ValueError("TRIPDATA_YEARS must contain at least one year.")
    return years


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / os.getenv("DATA_ROOT", "data")
    manifest_dir = data_root / "manifests"
    raw_zip_dir = data_root / "raw" / "zip"
    raw_csv_dir = data_root / "raw" / "csv"
    processed_dir = data_root / "processed"
    outputs_dir = project_root / "outputs"
    docs_dir = project_root / "docs"

    return Settings(
        project_root=project_root,
        data_root=data_root,
        manifest_dir=manifest_dir,
        raw_zip_dir=raw_zip_dir,
        raw_csv_dir=raw_csv_dir,
        processed_dir=processed_dir,
        outputs_dir=outputs_dir,
        docs_dir=docs_dir,
        manifest_name=os.getenv("MANIFEST_NAME", "tripdata_manifest_2024_2025.json"),
        years=_parse_years(os.getenv("TRIPDATA_YEARS", "2024,2025")),
        local_mongo_uri=os.getenv(
            "LOCAL_MONGO_URI",
            "mongodb://bigdata:bigdata@localhost:27018/?authSource=admin",
        ),
        local_mongo_db=os.getenv("LOCAL_MONGO_DB", "tripdata_local"),
        atlas_mongo_uri=os.getenv("ATLAS_MONGO_URI", ""),
        atlas_mongo_db=os.getenv("ATLAS_MONGO_DB", "tripdata_analytics"),
        atlas_results_collection=os.getenv("ATLAS_RESULTS_COLLECTION", "mapreduce_results"),
        webhdfs_url=os.getenv("WEBHDFS_URL", "http://localhost:9870"),
        hdfs_user=os.getenv("HDFS_USER", "root"),
        hdfs_raw_dir=os.getenv("HDFS_RAW_DIR", "/tripdata/raw"),
        hdfs_processed_dir=os.getenv("HDFS_PROCESSED_DIR", "/tripdata/processed"),
    )


SETTINGS = get_settings()
