from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import requests

from bigdata_project.config import SETTINGS


def _webhdfs_url(path: str, operation: str) -> str:
    normalized_path = quote(path.lstrip("/"))
    return (
        f"{SETTINGS.webhdfs_url}/webhdfs/v1/{normalized_path}"
        f"?op={operation}&user.name={SETTINGS.hdfs_user}"
    )


def _rewrite_redirect_url(redirect_url: str) -> str:
    redirect_parts = urlparse(redirect_url)
    external_parts = urlparse(SETTINGS.webhdfs_url)
    netloc = external_parts.hostname or redirect_parts.hostname or "localhost"
    if redirect_parts.port:
        netloc = f"{netloc}:{redirect_parts.port}"
    return urlunparse(redirect_parts._replace(netloc=netloc))


def ensure_hdfs_dir(path: str) -> None:
    response = requests.put(_webhdfs_url(path, "MKDIRS"), timeout=60)
    if response.status_code == 403 and SETTINGS.hdfs_user != "root":
        raise PermissionError(
            "HDFS denied write access for the configured user. "
            "Set HDFS_USER=root in .env for the provided Docker setup."
        )
    response.raise_for_status()


def upload_file_to_hdfs(local_path: Path, hdfs_path: str, overwrite: bool = True) -> None:
    create_url = (
        f"{_webhdfs_url(hdfs_path, 'CREATE')}"
        f"&overwrite={'true' if overwrite else 'false'}"
    )
    response = requests.put(create_url, allow_redirects=False, timeout=60)
    if response.status_code == 403 and SETTINGS.hdfs_user != "root":
        raise PermissionError(
            "HDFS denied upload access for the configured user. "
            "Set HDFS_USER=root in .env for the provided Docker setup."
        )
    response.raise_for_status()
    redirect_url = _rewrite_redirect_url(response.headers["Location"])

    with local_path.open("rb") as file_handle:
        upload_response = requests.put(redirect_url, data=file_handle, timeout=300)
    upload_response.raise_for_status()
