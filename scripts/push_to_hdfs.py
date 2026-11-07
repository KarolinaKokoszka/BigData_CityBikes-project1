from __future__ import annotations

import argparse

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.hdfs_ops import ensure_hdfs_dir, upload_file_to_hdfs
from bigdata_project.manifest import ensure_directories, load_manifest, select_entries
from bigdata_project.mongo_ops import get_local_database, record_import_status

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload selected raw ZIP archives to HDFS.")
    parser.add_argument("--year", type=int, help="Only process a single year.")
    parser.add_argument("--month", type=int, help="Only process a single month.")
    parser.add_argument("--limit", type=int, help="Only process the first N manifest entries.")
    return parser.parse_args()


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
    ensure_hdfs_dir(SETTINGS.hdfs_raw_dir)

    for entry in entries:
        archive_path = SETTINGS.raw_zip_dir / entry["file_name"]
        if not archive_path.exists():
            raise FileNotFoundError(
                f"Missing archive {archive_path}. Run scripts/download_and_stage.py first."
            )

        hdfs_dir = f"{SETTINGS.hdfs_raw_dir}/year={entry['year']}/month={entry['month']:02d}"
        hdfs_path = f"{hdfs_dir}/{entry['file_name']}"

        ensure_hdfs_dir(f"{SETTINGS.hdfs_raw_dir}/year={entry['year']}")
        ensure_hdfs_dir(hdfs_dir)
        upload_file_to_hdfs(archive_path, hdfs_path)

        record_import_status(
            db,
            file_name=entry["file_name"] + "#hdfs_raw",
            status="uploaded_hdfs_raw",
            extracted_files=[str(archive_path)],
            details={"hdfs_path": hdfs_path},
        )
        print(f"Uploaded {archive_path} -> {hdfs_path}")


if __name__ == "__main__":
    main()