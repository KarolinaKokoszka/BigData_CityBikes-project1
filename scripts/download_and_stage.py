from __future__ import annotations

import argparse

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.download import download_file, extract_zip, write_stage_report
from bigdata_project.manifest import ensure_directories, load_manifest, select_entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and extract selected tripdata archives.")
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
    report: list[dict] = []

    for entry in entries:
        archive_path = SETTINGS.raw_zip_dir / entry["file_name"]
        csv_output_dir = SETTINGS.raw_csv_dir / str(entry["year"]) / f"{entry['month']:02d}"

        downloaded = download_file(entry["url"], archive_path)
        extracted = extract_zip(downloaded, csv_output_dir)
        report.append(
            {
                "file_name": entry["file_name"],
                "archive_path": str(downloaded),
                "extracted_files": [str(path) for path in extracted],
                "stage_status": "completed",
            }
        )
        print(f"Staged {entry['file_name']} -> {csv_output_dir}")

    output_path = write_stage_report(report)
    print(f"Stage report written to {output_path}")


if __name__ == "__main__":
    main()
