from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from bigdata_project.config import SETTINGS

HTML_INDEX_URL = "https://s3.amazonaws.com/tripdata/index.html"
XML_INDEX_URL = "https://s3.amazonaws.com/tripdata?list-type=2"
DOWNLOAD_BASE_URL = "https://s3.amazonaws.com/tripdata/"
MONTHLY_FILE_PATTERN = re.compile(
    r"^(?P<year>\d{4})(?P<month>\d{2})-citibike-tripdata(?:[_-].+)?\.zip$"
)


@dataclass(frozen=True)
class ManifestEntry:
    file_name: str
    year: int
    month: int
    url: str
    size_bytes: int | None
    last_modified: str | None
    source_type: str
    status: str = "pending"


def ensure_directories() -> None:
    for path in (
        SETTINGS.manifest_dir,
        SETTINGS.raw_zip_dir,
        SETTINGS.raw_csv_dir,
        SETTINGS.processed_dir,
        SETTINGS.outputs_dir,
        SETTINGS.docs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def fetch_html_index(session: requests.Session | None = None) -> str:
    session = session or requests.Session()
    response = session.get(HTML_INDEX_URL, timeout=60)
    response.raise_for_status()
    return response.text


def fetch_xml_index(session: requests.Session | None = None) -> str:
    session = session or requests.Session()
    response = session.get(XML_INDEX_URL, timeout=60)
    response.raise_for_status()
    return response.text


def parse_html_keys(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    keys: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if href.endswith(".zip"):
            keys.append(Path(href).name)
    return keys


def parse_xml_entries(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    records: list[dict[str, str]] = []
    for content in root.findall("s3:Contents", namespace):
        key = content.findtext("s3:Key", default="", namespaces=namespace)
        size = content.findtext("s3:Size", default="", namespaces=namespace)
        last_modified = content.findtext(
            "s3:LastModified", default="", namespaces=namespace
        )
        records.append(
            {
                "key": key,
                "size": size,
                "last_modified": last_modified,
            }
        )
    return records


def filter_monthly_archives(
    keys: Iterable[str],
    years: tuple[int, ...] | None = None,
) -> list[ManifestEntry]:
    allowed_years = set(years or SETTINGS.years)
    entries: list[ManifestEntry] = []

    for key in keys:
        match = MONTHLY_FILE_PATTERN.match(key)
        if not match:
            continue
        year = int(match.group("year"))
        month = int(match.group("month"))
        if year not in allowed_years:
            continue
        entries.append(
            ManifestEntry(
                file_name=key,
                year=year,
                month=month,
                url=f"{DOWNLOAD_BASE_URL}{key}",
                size_bytes=None,
                last_modified=None,
                source_type="html",
            )
        )

    return sorted(entries, key=lambda item: (item.year, item.month, item.file_name))


def select_entries(
    entries: Iterable[ManifestEntry | dict],
    year: int | None = None,
    month: int | None = None,
    limit: int | None = None,
) -> list[ManifestEntry | dict]:
    filtered = []
    for entry in entries:
        entry_year = entry.year if isinstance(entry, ManifestEntry) else entry["year"]
        entry_month = entry.month if isinstance(entry, ManifestEntry) else entry["month"]
        if year is not None and entry_year != year:
            continue
        if month is not None and entry_month != month:
            continue
        filtered.append(entry)
    if limit is not None:
        return filtered[:limit]
    return filtered


def build_manifest(
    years: tuple[int, ...] | None = None,
    session: requests.Session | None = None,
) -> list[ManifestEntry]:
    ensure_directories()
    session = session or requests.Session()

    html_keys = parse_html_keys(fetch_html_index(session))
    html_entries = filter_monthly_archives(html_keys, years=years)
    if html_entries:
        return html_entries

    xml_records = parse_xml_entries(fetch_xml_index(session))
    allowed_years = set(years or SETTINGS.years)
    entries: list[ManifestEntry] = []
    for record in xml_records:
        key = record["key"]
        match = MONTHLY_FILE_PATTERN.match(key)
        if not match:
            continue
        year = int(match.group("year"))
        month = int(match.group("month"))
        if year not in allowed_years:
            continue
        entries.append(
            ManifestEntry(
                file_name=key,
                year=year,
                month=month,
                url=f"{DOWNLOAD_BASE_URL}{key}",
                size_bytes=int(record["size"]) if record["size"] else None,
                last_modified=record["last_modified"] or None,
                source_type="xml-fallback",
            )
        )
    return sorted(entries, key=lambda item: (item.year, item.month, item.file_name))


def save_manifest(
    entries: list[ManifestEntry],
    output_path: Path | None = None,
    years: tuple[int, ...] | None = None,
) -> Path:
    ensure_directories()
    output_path = output_path or (SETTINGS.manifest_dir / SETTINGS.manifest_name)
    payload = {
        "years": list(years or SETTINGS.years),
        "format": "zip archives containing csv files",
        "entry_count": len(entries),
        "entries": [asdict(entry) for entry in entries],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def load_manifest(path: Path | None = None) -> dict:
    manifest_path = path or (SETTINGS.manifest_dir / SETTINGS.manifest_name)
    return json.loads(manifest_path.read_text(encoding="utf-8"))
