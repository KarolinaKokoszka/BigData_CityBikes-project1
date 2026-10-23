import pandas as pd

from bigdata_project.transform import normalize_chunk


def test_normalize_chunk_drops_invalid_rows_and_adds_features():
    frame = pd.DataFrame(
        [
            {
                "ride_id": "ok-1",
                "rideable_type": "classic_bike",
                "started_at": "2024-01-01T10:00:00",
                "ended_at": "2024-01-01T10:15:00",
                "start_station_name": "A",
                "start_station_id": "1",
                "end_station_name": "B",
                "end_station_id": "2",
                "start_lat": 1.0,
                "start_lng": 2.0,
                "end_lat": 3.0,
                "end_lng": 4.0,
                "member_casual": "member",
            },
            {
                "ride_id": "bad-1",
                "rideable_type": "classic_bike",
                "started_at": "2024-01-01T10:15:00",
                "ended_at": "2024-01-01T10:00:00",
                "start_station_name": "A",
                "start_station_id": "1",
                "end_station_name": "B",
                "end_station_id": "2",
                "start_lat": 1.0,
                "start_lng": 2.0,
                "end_lat": 3.0,
                "end_lng": 4.0,
                "member_casual": "member",
            },
        ]
    )

    normalized = normalize_chunk(frame, "sample.csv")

    assert len(normalized.index) == 1
    assert normalized.iloc[0]["trip_duration_minutes"] == 15.0
    assert normalized.iloc[0]["trip_year"] == 2024
    assert normalized.iloc[0]["source_file"] == "sample.csv"
