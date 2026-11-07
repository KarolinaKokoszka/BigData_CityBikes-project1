from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from bigdata_project.config import SETTINGS

SYSTEM_DATA_URL = "https://citibikenyc.com/system-data"
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


def fetch_system_data_page(session: requests.Session | None = None) -> str:
    session = session or requests.Session()
    response = session.get(SYSTEM_DATA_URL, timeout=60)
    response.raise_for_status()
    return response.text


def fetch_text(url: str, session: requests.Session | None = None) -> str:
    session = session or requests.Session()
    response = session.get(url, timeout=60)
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


def parse_system_data_listing_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    listing_urls: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        absolute_url = urljoin(SYSTEM_DATA_URL, href)
        if "s3.amazonaws.com/tripdata" not in absolute_url:
            continue
        if absolute_url.endswith(".zip"):
            continue
        if absolute_url.endswith("index.html") or "list-type=2" in absolute_url:
            if absolute_url not in listing_urls:
                listing_urls.append(absolute_url)
    return listing_urls


def parse_system_data_page_details(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    page_title = ""
    title_node = soup.find("h1")
    if title_node:
        page_title = title_node.get_text(" ", strip=True)
    if not page_title:
        title_meta = soup.find("meta", attrs={"property": "og:title"})
        if title_meta:
            page_title = title_meta.get("content", "").strip()

    page_description = ""
    description_node = soup.find("meta", attrs={"name": "description"})
    if description_node:
        page_description = description_node.get("content", "").strip()

    section_title = ""
    field_names: list[str] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = heading.get_text(" ", strip=True)
        if "Citi Bike Trip Histories" not in heading_text:
            continue
        section_title = heading_text
        field_list = heading.find_next("ul")
        if field_list:
            for item in field_list.find_all("li"):
                text = item.get_text(" ", strip=True)
                if text:
                    field_names.append(text)
        break

    return {
        "page_title": page_title,
        "page_description": page_description,
        "trip_history_section_title": section_title,
        "trip_history_fields": field_names,
    }


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
    source_type: str = "html",
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
                source_type=source_type,
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


def build_scrape_report(
    page_details: dict,
    listing_urls: list[str],
    selected_listing_url: str | None,
    years: tuple[int, ...],
    entry_count: int,
    source_type: str,
) -> dict:
    return {
        "page_url": SYSTEM_DATA_URL,
        "page_title": page_details.get("page_title", ""),
        "page_description": page_details.get("page_description", ""),
        "trip_history_section_title": page_details.get("trip_history_section_title", ""),
        "trip_history_fields": page_details.get("trip_history_fields", []),
        "listing_urls": listing_urls,
        "listing_url_count": len(listing_urls),
        "selected_listing_url": selected_listing_url,
        "years": list(years),
        "manifest_entry_count": entry_count,
        "manifest_source": source_type,
    }


def save_scrape_report(report: dict, output_path: Path | None = None) -> Path:
    ensure_directories()
    output_path = output_path or (SETTINGS.outputs_dir / "system_data_scrape.json")
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path


def _build_entries_from_xml_records(
    xml_records: list[dict[str, str]],
    years: tuple[int, ...] | None = None,
) -> list[ManifestEntry]:
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


def build_manifest_bundle(
    years: tuple[int, ...] | None = None,
    session: requests.Session | None = None,
) -> tuple[list[ManifestEntry], dict]:
    ensure_directories()
    session = session or requests.Session()
    selected_years = years or SETTINGS.years

    system_data_html = fetch_system_data_page(session)
    page_details = parse_system_data_page_details(system_data_html)
    listing_urls = parse_system_data_listing_urls(system_data_html)

    for listing_url in listing_urls:
        listing_html = fetch_text(listing_url, session)
        html_entries = filter_monthly_archives(
            parse_html_keys(listing_html),
            years=selected_years,
            source_type="system-data-html",
        )
        if html_entries:
            report = build_scrape_report(
                page_details=page_details,
                listing_urls=listing_urls,
                selected_listing_url=listing_url,
                years=selected_years,
                entry_count=len(html_entries),
                source_type="system-data-html",
            )
            return html_entries, report

    html_entries = filter_monthly_archives(
        parse_html_keys(fetch_html_index(session)),
        years=selected_years,
        source_type="s3-html-fallback",
    )
    if html_entries:
        report = build_scrape_report(
            page_details=page_details,
            listing_urls=listing_urls,
            selected_listing_url=HTML_INDEX_URL,
            years=selected_years,
            entry_count=len(html_entries),
            source_type="s3-html-fallback",
        )
        return html_entries, report

    xml_entries = _build_entries_from_xml_records(
        parse_xml_entries(fetch_xml_index(session)),
        years=selected_years,
    )
    report = build_scrape_report(
        page_details=page_details,
        listing_urls=listing_urls,
        selected_listing_url=XML_INDEX_URL,
        years=selected_years,
        entry_count=len(xml_entries),
        source_type="xml-fallback",
    )
    return xml_entries, report


def build_manifest(
    years: tuple[int, ...] | None = None,
    session: requests.Session | None = None,
) -> list[ManifestEntry]:
    entries, _report = build_manifest_bundle(years=years, session=session)
    return entries


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
