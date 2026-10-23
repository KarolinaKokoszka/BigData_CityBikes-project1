from __future__ import annotations

import json
import shutil
import time
import zipfile
from pathlib import Path

import requests

from bigdata_project.config import SETTINGS
from bigdata_project.manifest import ensure_directories


def download_file(
    url: str,
    destination: Path,
    chunk_size: int = 1024 * 1024,
    retries: int = 5,
) -> Path:
    ensure_directories()
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        if zipfile.is_zipfile(destination):
            return destination
        print(f"Removing incomplete archive {destination.name}")
        destination.unlink()

    part_path = destination.with_name(destination.name + ".part")
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=(15, 120)) as response:
                response.raise_for_status()
                expected_size = int(response.headers.get("Content-Length", 0))
                with part_path.open("wb") as file_handle:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file_handle.write(chunk)
            if expected_size and part_path.stat().st_size != expected_size:
                raise OSError(
                    f"Incomplete download: {part_path.stat().st_size} of {expected_size} bytes"
                )
            part_path.replace(destination)
            return destination
        except (requests.RequestException, OSError) as error:
            last_error = error
            print(f"Download attempt {attempt}/{retries} failed for {destination.name}: {error}")
            time.sleep(5 * attempt)

    raise RuntimeError(f"Could not download {url} after {retries} attempts") from last_error


def extract_zip(archive_path: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_files: list[Path] = []
    with zipfile.ZipFile(archive_path, "r") as archive:
        for member in archive.namelist():
            if member.endswith("/"):
                continue
            target_path = output_dir / Path(member).name
            if target_path.exists():
                extracted_files.append(target_path)
                continue
            temp_path = target_path.with_name(target_path.name + ".part")
            with archive.open(member) as source, temp_path.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            temp_path.replace(target_path)
            extracted_files.append(target_path)
    return extracted_files


def write_stage_report(report: list[dict], output_path: Path | None = None) -> Path:
    ensure_directories()
    output_path = output_path or (SETTINGS.outputs_dir / "stage_report.json")
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path