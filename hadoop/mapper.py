from __future__ import annotations

import csv
import sys


def emit(metric: str, dimension: str, duration: float) -> None:
    print(f"{metric}\t{dimension}\t1\t{duration}")


def main() -> None:
    reader = csv.DictReader(sys.stdin, delimiter="\t")
    for row in reader:
        try:
            duration = float(row["trip_duration_minutes"])
        except (TypeError, ValueError):
            continue

        month_key = f"{row['trip_year']}-{str(row['trip_month']).zfill(2)}"
        emit("rides_by_month", month_key, duration)
        emit("duration_by_member_type", row["member_casual"], duration)
        emit("rides_by_bike_type", row["rideable_type"], duration)
        emit("rides_by_day_of_week", row["trip_day_of_week"], duration)
        emit("rides_by_start_station", row["start_station_name"], duration)


if __name__ == "__main__":
    main()
