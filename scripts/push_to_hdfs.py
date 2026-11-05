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
] # kolumny do analiz

# argumenty na potrzeby testów
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare TSV files and upload them to HDFS.")
    parser.add_argument("--year", type=int, help="Only process a single year.")
    parser.add_argument("--month", type=int, help="Only process a single month.")
    parser.add_argument("--limit", type=int, help="Only process the first N manifest entries.")
    return parser.parse_args()


def write_monthly_tsv(csv_file: Path, output_dir: Path) -> Path:
    """
    Istniejący plik TSV jest używany ponownie, więc po zmianie reguł
    czyszczenia trzeba usunąć folder data/processed przed ponownym uruchomieniem!!!
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{csv_file.stem}.tsv"
    if output_path.exists():
        return output_path

    temp_path = output_path.with_name(output_path.name + ".part") # pliki tymczasowe - zabezpieczenie gdyby skrypt padł w trakcie
    with temp_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.writer(file_handle, delimiter="\t")
        # czytanie csv partiami
        for chunk in iter_csv_chunks(csv_file):
            normalized = normalize_chunk(chunk, csv_file.name)
            writer.writerows(normalized[HADOOP_COLUMNS].itertuples(index=False, name=None))
    temp_path.replace(output_path) #plik włściwy
    return output_path


def main() -> None:
    args = parse_args()
    ensure_directories()

    # wczytaie lisy archiwów i wybór wpisów na podstawie argumentów
    manifest = load_manifest()
    entries = select_entries(
        manifest["entries"],
        year=args.year,
        month=args.month,
        limit=args.limit,
    )

    db = get_local_database()
    ensure_hdfs_dir(SETTINGS.hdfs_processed_dir)

    # pętla po wybranych miesącach
    for entry in entries:
        csv_dir = SETTINGS.raw_csv_dir / str(entry["year"]) / f"{entry['month']:02d}"
        processed_dir = SETTINGS.processed_dir / str(entry["year"]) / f"{entry['month']:02d}"
        # pętla po CSV z danego miesiąca
        for csv_file in sorted(csv_dir.glob("*.csv")):
            local_tsv = write_monthly_tsv(csv_file, processed_dir)
            hdfs_path = (
                f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}/"
                f"month={entry['month']:02d}/{local_tsv.name}"
            )

            # utworzenie katalogów w HDFS
            ensure_hdfs_dir(f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}")
            ensure_hdfs_dir(f"{SETTINGS.hdfs_processed_dir}/year={entry['year']}/month={entry['month']:02d}")
            
            upload_file_to_hdfs(local_tsv, hdfs_path) # wysłanie pliku TSV do HDFS

            # zapis statusu w lokalnym MongoDB, 
            # "#hdfs" odróżnia ten wpis od statusu importu do Mongo dla tego samego archiwum.
            record_import_status(
                db,
                file_name=entry["file_name"] + "#hdfs",
                status="uploaded_hdfs",
                extracted_files=[str(csv_file)],
                details={"hdfs_path": hdfs_path},
            )
            print(f"Uploaded {local_tsv} -> {hdfs_path}")


if __name__ == "__main__":
    main()