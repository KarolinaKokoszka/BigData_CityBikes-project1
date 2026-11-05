from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.transform import iter_csv_chunks, normalize_chunk


def load_all_normalized_rows() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    #czytanie wszystkich lokalnych CSV i zastosowanie tej samej logiki czyszczenia co w imporcie do MongoDB
    for csv_file in sorted(SETTINGS.raw_csv_dir.rglob("*.csv")):
        for chunk in iter_csv_chunks(csv_file, chunksize=50_000):
            frames.append(normalize_chunk(chunk, csv_file.name))
    if not frames:
        raise FileNotFoundError("No CSV files found in data/raw/csv.")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    SETTINGS.outputs_dir.mkdir(parents=True, exist_ok=True)
    df = load_all_normalized_rows()

    # analiza 1: liczba przejazdów w każdym miesiącu (grupowanie po roku i miesiącu)
    monthly_trips = df.groupby(["trip_year", "trip_month"]).size().rename("ride_count")
    
    # analiza 2: średni czas przejazdu dla każdego typu klienta (member / casual)
    avg_duration = df.groupby("member_casual")["trip_duration_minutes"].mean().round(2)
    
    # analiza 3: liczba przejazdów według typu roweru, od najpopularniejszego
    bike_share = (
        df.groupby("rideable_type").size().sort_values(ascending=False).rename("ride_count")
    )

    # analiza 4: 10 najpopularniejszych stacji startowych
    top_start_stations = (
        df.groupby("start_station_name")
        .size()
        .sort_values(ascending=False)
        .head(10)
        .rename("ride_count")
    )

    # zapis wyników
    monthly_trips.to_csv(SETTINGS.outputs_dir / "monthly_trips.csv")
    avg_duration.to_csv(SETTINGS.outputs_dir / "avg_duration_by_member_type.csv")
    bike_share.to_csv(SETTINGS.outputs_dir / "bike_type_share.csv")
    top_start_stations.to_csv(SETTINGS.outputs_dir / "top_start_stations.csv")

    summary = {
        "row_count": int(len(df.index)),
        "unique_rides": int(df["ride_id"].nunique()),
        "member_categories": sorted(df["member_casual"].dropna().unique().tolist()),
        "bike_types": sorted(df["rideable_type"].dropna().unique().tolist()),
    }
    (SETTINGS.outputs_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(f"Saved local statistics to {SETTINGS.outputs_dir}")


if __name__ == "__main__":
    main()
