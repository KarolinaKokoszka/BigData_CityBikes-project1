from __future__ import annotations

import argparse
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.download import extract_zip
from bigdata_project.hdfs_ops import download_file_from_hdfs, ensure_hdfs_dir, upload_file_to_hdfs
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
    parser = argparse.ArgumentParser(
        description="Prepare temporary TSV input for Hadoop Streaming and upload it to HDFS."
    )
    parser.add_argument("--year", type=int, help="Only process a single year.")
    parser.add_argument("--month", type=int, help="Only process a single month.")
    parser.add_argument("--limit", type=int, help="Only process the first N manifest entries.")
    return parser.parse_args()


def write_monthly_tsv(csv_file: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{csv_file.stem}.tsv"
    if output_path.exists():
        return output_path

    temp_path = output_path.with_name(output_path.name + ".part")
    with temp_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.writer(file_handle, delimiter="\t")
        for chunk in iter_csv_chunks(csv_file):
            normalized = normalize_chunk(chunk, csv_file.name)
            writer.writerows(normalized[HADOOP_COLUMNS].itertuples(index=False, name=None))
    temp_path.replace(output_path)
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
    ensure_hdfs_dir(SETTINGS.hdfs_mapreduce_input_dir)

    for entry in entries:
        processed_dir = SETTINGS.processed_dir / str(entry["year"]) / f"{entry['month']:02d}"
        raw_hdfs_dir = f"{SETTINGS.hdfs_raw_dir}/year={entry['year']}/month={entry['month']:02d}"
        raw_hdfs_path = f"{raw_hdfs_dir}/{entry['file_name']}"

        with TemporaryDirectory(prefix="mr_input_") as temp_dir:
            temp_root = Path(temp_dir)
            local_zip = download_file_from_hdfs(raw_hdfs_path, temp_root / entry["file_name"])
            extracted_dir = temp_root / "csv"
            extracted_files = extract_zip(local_zip, extracted_dir)

            for csv_file in sorted(extracted_files):
                local_tsv = write_monthly_tsv(csv_file, processed_dir)
                hdfs_dir = (
                    f"{SETTINGS.hdfs_mapreduce_input_dir}/year={entry['year']}/"
                    f"month={entry['month']:02d}"
                )
                hdfs_path = f"{hdfs_dir}/{local_tsv.name}"

                ensure_hdfs_dir(f"{SETTINGS.hdfs_mapreduce_input_dir}/year={entry['year']}")
                ensure_hdfs_dir(hdfs_dir)
                upload_file_to_hdfs(local_tsv, hdfs_path)

                record_import_status(
                    db,
                    file_name=entry["file_name"] + "#mr_input",
                    status="prepared_mapreduce_input",
                    extracted_files=[str(local_zip)],
                    details={"raw_hdfs_path": raw_hdfs_path, "hdfs_path": hdfs_path},
                )
                print(f"Prepared Hadoop input {raw_hdfs_path} -> {hdfs_path}")


if __name__ == "__main__":
    main()
