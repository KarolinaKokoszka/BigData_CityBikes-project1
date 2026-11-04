import sys
from collections import defaultdict


def main():
    acc = defaultdict(lambda: [0, 0.0, 0.0])  # count, sum, sum of squares
    for line in sys.stdin:
        f = line.rstrip("\n").split("\t")
        if len(f) != 9 or f[0] == "trip_year":
            continue
        try:
            d = float(f[8])
        except ValueError:
            continue

        year, month, dow, hour, member, bike, start_station, _end, _dur = f
        keys = [
            ("rides_by_month", "{}-{}".format(year, month.zfill(2))),
            ("duration_by_member_type", member),
            ("rides_by_bike_type", bike),
            ("rides_by_day_of_week", dow),
            ("rides_by_hour", "{}|{}".format(hour.zfill(2), member)),
            # Keep missing stations under the same metric as pandas verification.
            ("rides_by_start_station", start_station),
        ]

        for metric, dimension in keys:
            a = acc["{}|{}".format(metric, dimension)]
            a[0] += 1
            a[1] += d
            a[2] += d * d

    for key, a in acc.items():
        print("{}\t{}\t{}\t{}".format(key, a[0], repr(a[1]), repr(a[2])))


if __name__ == "__main__":
    main()