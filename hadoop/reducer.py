from __future__ import annotations

import sys


def flush(metric: str | None, dimension: str | None, count: int, duration_sum: float) -> None:
    if metric is None or dimension is None:
        return
    print(f"{metric}\t{dimension}\t{count}\t{duration_sum:.4f}")


def main() -> None:
    current_metric = None
    current_dimension = None
    current_count = 0
    current_duration = 0.0

    for line in sys.stdin:
        parts = line.strip().split("\t")
        if len(parts) != 4:
            continue
        metric, dimension, count, duration = parts
        count_value = int(float(count))
        duration_value = float(duration)

        if (metric, dimension) != (current_metric, current_dimension):
            flush(current_metric, current_dimension, current_count, current_duration)
            current_metric = metric
            current_dimension = dimension
            current_count = 0
            current_duration = 0.0

        current_count += count_value
        current_duration += duration_value

    flush(current_metric, current_dimension, current_count, current_duration)


if __name__ == "__main__":
    main()
