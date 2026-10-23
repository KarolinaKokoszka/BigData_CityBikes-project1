import argparse
import math

import pandas as pd

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.transform import iter_csv_chunks, normalize_chunk


def parse_args():
    parser = argparse.ArgumentParser(description="Compare MapReduce results with pandas for one month.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    return parser.parse_args()


def load_month(year, month):
    csv_dir = SETTINGS.raw_csv_dir / str(year) / "{:02d}".format(month)
    frames, raw_rows = [], 0
    for csv_file in sorted(csv_dir.glob("*.csv")):
        for chunk in iter_csv_chunks(csv_file):
            raw_rows += len(chunk.index)
            frames.append(normalize_chunk(chunk, csv_file.name))
    return pd.concat(frames, ignore_index=True), raw_rows


def expected_stats(df):
    d = df["trip_duration_minutes"]
    keys = {
        "rides_by_month": df["trip_year"].astype(str) + "-" + df["trip_month"].map("{:02d}".format),
        "duration_by_member_type": df["member_casual"],
        "rides_by_bike_type": df["rideable_type"],
        "rides_by_day_of_week": df["trip_day_of_week"],
        "rides_by_start_station": df["start_station_name"],
        "rides_by_hour": df["trip_hour"].map("{:02d}".format) + "|" + df["member_casual"],
    }
    result = {}
    for metric, key in keys.items():
        grouped = d.groupby(key)
        stats = pd.DataFrame({
            "n": grouped.count(), "sum": grouped.sum(),
            "mean": grouped.mean(), "std": grouped.std(ddof=0),
        })
        for dimension, row in stats.iterrows():
            result[(metric, str(dimension))] = row
    return result


def load_job_results():
    path = SETTINGS.outputs_dir / "mapreduce_results.tsv"
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) == 6:
            result[(p[0], p[1])] = [int(p[2]), float(p[3]), float(p[4]), float(p[5])]
    return result


def main():
    args = parse_args()
    df, raw_rows = load_month(args.year, args.month)
    print("Wiersze wejsciowe (CSV): {}".format(raw_rows))
    print("Wiersze po czyszczeniu: {}".format(len(df.index)))
    print("Odrzucone: {}".format(raw_rows - len(df.index)))

    expected = expected_stats(df)
    job = load_job_results()

    mismatches = 0
    for key, row in expected.items():
        got = job.get(key)
        if got is None:
            mismatches += 1
            print("BRAK w wyniku joba:", key)
            continue
        ok = (
            got[0] == int(row["n"])
            and math.isclose(got[1], row["sum"], rel_tol=1e-9, abs_tol=1e-3)
            and math.isclose(got[2], row["mean"], abs_tol=1e-4)
            and math.isclose(got[3], row["std"], abs_tol=1e-4)
        )
        if not ok:
            mismatches += 1
            print("ROZNICA:", key, "job:", got, "pandas:", row.tolist())
    extra = set(job) - set(expected)
    for key in sorted(extra):
        mismatches += 1
        print("NADMIAR w wyniku joba:", key)

    print("Porownano grup: {}, niezgodnosci: {}".format(len(expected), mismatches))


if __name__ == "__main__":
    main()