from __future__ import annotations

import json
import zipfile
from pathlib import Path

import requests

from bigdata_project.config import SETTINGS
from bigdata_project.manifest import ensure_directories


def download_file(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> Path:
    ensure_directories()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file_handle.write(chunk)
    return destination


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
            with archive.open(member) as source, target_path.open("wb") as target:
                target.write(source.read())
            extracted_files.append(target_path)
    return extracted_files


def write_stage_report(report: list[dict], output_path: Path | None = None) -> Path:
    ensure_directories()
    output_path = output_path or (SETTINGS.outputs_dir / "stage_report.json")
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path
