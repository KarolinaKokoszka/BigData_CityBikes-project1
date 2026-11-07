from __future__ import annotations

import argparse

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.manifest import build_manifest_bundle, save_manifest, save_scrape_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build tripdata manifest for selected years.")
    parser.add_argument(
        "--years",
        default=",".join(str(year) for year in SETTINGS.years),
        help="Comma-separated years, for example 2024,2025",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    years = tuple(int(part.strip()) for part in args.years.split(",") if part.strip())
    manifest, scrape_report = build_manifest_bundle(years=years)
    output_path = save_manifest(manifest, years=years)
    scrape_path = save_scrape_report(scrape_report)
    print(
        f"Saved {len(manifest)} monthly archives for years {years} "
        f"to {output_path}"
    )
    print(f"Saved system-data scraping report to {scrape_path}")


if __name__ == "__main__":
    main()
