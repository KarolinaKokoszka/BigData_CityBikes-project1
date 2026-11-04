from __future__ import annotations

import json

from bootstrap import setup_project_root

setup_project_root()

from bigdata_project.config import SETTINGS
from bigdata_project.mongo_ops import write_results_to_atlas


def parse_result_line(line: str) -> dict:
    parts = line.strip().split("\t")
    if len(parts) not in (4, 6):
        raise ValueError(f"Unexpected reducer line: {line}")

    if len(parts) == 4:
        metric, dimension, count, duration_sum = parts
        payload = {
            "metric": metric,
            "dimension": dimension,
            "ride_count": int(float(count)),
            "duration_sum_minutes": float(duration_sum),
        }
        payload["average_duration_minutes"] = (
            payload["duration_sum_minutes"] / payload["ride_count"]
            if payload["ride_count"]
            else 0.0
        )
        payload["duration_stddev_minutes"] = None
        return payload

    metric, dimension, count, duration_sum, duration_mean, duration_stddev = parts
    payload = {
        "metric": metric,
        "dimension": dimension,
        "ride_count": int(float(count)),
        "duration_sum_minutes": float(duration_sum),
        "average_duration_minutes": float(duration_mean),
        "duration_stddev_minutes": float(duration_stddev),
    }
    return payload


def main() -> None:
    result_file = SETTINGS.outputs_dir / "mapreduce_results.tsv"
    if not result_file.exists():
        raise FileNotFoundError(
            "Reducer output was not found. Save it first as outputs/mapreduce_results.tsv."
        )

    results = [parse_result_line(line) for line in result_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    stored = write_results_to_atlas(results)

    json_output = SETTINGS.outputs_dir / "atlas_results_preview.json"
    json_output.write_text(json.dumps(results[:50], indent=2), encoding="utf-8")
    print(f"Stored {stored} result documents in MongoDB Atlas.")
    print(f"Preview saved to {json_output}")


if __name__ == "__main__":
    main()
