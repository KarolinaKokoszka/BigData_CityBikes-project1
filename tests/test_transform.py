import pandas as pd

from bigdata_project.transform import normalize_chunk


def make_row(ride_id, started_at, ended_at, lat, lng):
    return {
        "ride_id": ride_id,
        "rideable_type": "classic_bike",
        "started_at": started_at,
        "ended_at": ended_at,
        "start_station_name": "A",
        "start_station_id": "1",
        "end_station_name": "B",
        "end_station_id": "2",
        "start_lat": lat,
        "start_lng": lng,
        "end_lat": 40.75,
        "end_lng": -73.98,
        "member_casual": "member",
    }


def test_normalize_chunk_drops_invalid_rows_and_adds_features():
    frame = pd.DataFrame(
        [
            make_row("ok-1", "2024-01-01T10:00:00", "2024-01-01T10:15:00", 40.73, -73.99),
            make_row("bad-1", "2024-01-01T10:15:00", "2024-01-01T10:00:00", 40.73, -73.99),
        ]
    )

    normalized = normalize_chunk(frame, "sample.csv")

    assert len(normalized.index) == 1
    assert normalized.iloc[0]["trip_duration_minutes"] == 15.0
    assert normalized.iloc[0]["trip_year"] == 2024
    assert normalized.iloc[0]["source_file"] == "sample.csv"


def test_normalize_chunk_drops_rows_starting_outside_nyc():
    frame = pd.DataFrame(
        [
            make_row("nyc", "2024-01-01T10:00:00", "2024-01-01T10:15:00", 40.73, -73.99),
            make_row("far-away", "2024-01-01T10:00:00", "2024-01-01T10:15:00", 1.0, 2.0),
        ]
    )

    normalized = normalize_chunk(frame, "sample.csv")

    assert normalized["ride_id"].tolist() == ["nyc"]