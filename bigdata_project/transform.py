from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd

REQUIRED_COLUMNS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "start_station_id",
    "end_station_name",
    "end_station_id",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
    "member_casual",
]

CSV_DTYPES = {
    "ride_id": "string",
    "rideable_type": "string",
    "start_station_name": "string",
    "start_station_id": "string",
    "end_station_name": "string",
    "end_station_id": "string",
    "member_casual": "string",
}

OUTPUT_COLUMNS = REQUIRED_COLUMNS + [
    "trip_duration_minutes",
    "trip_year",
    "trip_month",
    "trip_day_of_week",
    "trip_hour",
    "source_file",
]


def iter_csv_chunks(csv_path: Path, chunksize: int = 100_000) -> Iterator[pd.DataFrame]:
    yield from pd.read_csv(
        csv_path,
        chunksize=chunksize,
        dtype=CSV_DTYPES,
        low_memory=False,
    )


def normalize_chunk(chunk: pd.DataFrame, source_file: str) -> pd.DataFrame:
    frame = chunk.copy()
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in {source_file}: {missing_columns}")

    frame["started_at"] = pd.to_datetime(frame["started_at"], errors="coerce", utc=True)
    frame["ended_at"] = pd.to_datetime(frame["ended_at"], errors="coerce", utc=True)

    frame = frame.dropna(subset=["ride_id", "started_at", "ended_at", "member_casual"])
    frame = frame[frame["ended_at"] >= frame["started_at"]]

    frame["trip_duration_minutes"] = (
        frame["ended_at"] - frame["started_at"]
    ).dt.total_seconds() / 60.0
    frame = frame[frame["trip_duration_minutes"] <= 24 * 60]

    frame["trip_year"] = frame["started_at"].dt.year
    frame["trip_month"] = frame["started_at"].dt.month
    frame["trip_day_of_week"] = frame["started_at"].dt.day_name()
    frame["trip_hour"] = frame["started_at"].dt.hour
    frame["source_file"] = source_file

    for column in (
        "start_station_name",
        "start_station_id",
        "end_station_name",
        "end_station_id",
        "rideable_type",
        "member_casual",
    ):
        frame[column] = frame[column].fillna("unknown")

    numeric_columns = ["start_lat", "start_lng", "end_lat", "end_lng"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame[OUTPUT_COLUMNS]
    return frame


def dataframe_to_documents(frame: pd.DataFrame) -> list[dict]:
    records = frame.to_dict(orient="records")
    for record in records:
        record["_id"] = f"{record['ride_id']}::{record['source_file']}"
        record["started_at"] = record["started_at"].isoformat()
        record["ended_at"] = record["ended_at"].isoformat()
    return records
