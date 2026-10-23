from __future__ import annotations

import argparse
import csv
from pathlib import Path

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.hdfs_ops import ensure_hdfs_dir, upload_file_to_hdfs
from bigdata_project.manifest import ensure_directories, load_manifest, select_entries
from bigdata_project.mongo_ops import get_local_database, record_import_status
from bigdata_project.transform import iter_csv_chunks, normalize_chunk

HADOOP_COLUMNS = [
    "trip_year",
    "trip_month",
    "trip_day_of_week",
    "trip_hour",
    "member_casual",
    "rideable_type",
    "start_station_name",
    "end_station_name",
    "trip_duration_minutes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare TSV files and upload them to HDFS.")
    parser.add_argument("--year", type=int, help="Only process a single year.")
    parser.add_argument("--month", type=int, help="Only process a single month.")
    parser.add_argument("--limit", type=int, help="Only process the first N manifest entries.")
    return parser.parse_args()


def write_monthly_tsv(csv_file: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{csv_file.stem}.tsv"
    if output_path.exists():
        return output_path

    with output_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.writer(file_handle, delimiter="\t")
        writer.writerow(HADOOP_COLUMNS)
        for chunk in iter_csv_chunks(csv_file):
            normalized = normalize_chunk(chunk, csv_file.name)
            writer.writerows(normalized[HADOOP_COLUMNS].itertuples(index=False, name=None))
    return output_path


def main() -> None:
    args = parse_args()
    ensure_directories()
    manifest = load_manifest()
    entries = select_entries(
        manifest["entries"],
        year=args.year,
        month=args.month,
        limit=args.limit,
    )
    db = get_local_database()
    ensure_hdfs_dir(SETTINGS.hdfs_processed_dir)

    for entry in entries:
        csv_dir = SETTINGS.raw_csv_dir / str(entry["year"]) / f"{entry['month']:02d}"
        processed_dir = SETTINGS.processed_dir / str(entry["year"]) / f"{entry['month']:02d}"
        for csv_file in sorted(csv_dir.glob("*.csv")):
            local_tsv = write_monthly_tsv(csv_file, processed_dir)
            hdfs_path = (
                f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}/"
                f"month={entry['month']:02d}/{local_tsv.name}"
            )
            ensure_hdfs_dir(f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}")
            ensure_hdfs_dir(
                f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}/month={entry['month']:02d}"
            )
            upload_file_to_hdfs(local_tsv, hdfs_path)
            record_import_status(
                db,
                file_name=entry["file_name"],
                status="uploaded_hdfs",
                extracted_files=[str(csv_file)],
                details={"hdfs_path": hdfs_path},
            )
            print(f"Uploaded {local_tsv} -> {hdfs_path}")


if __name__ == "__main__":
    main()
