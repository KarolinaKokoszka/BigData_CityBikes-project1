from bigdata_project.manifest import filter_monthly_archives, parse_html_keys


def test_parse_html_keys_extracts_zip_links():
    html = """
    <html><body>
      <a href="202401-citibike-tripdata.zip">202401</a>
      <a href="notes.txt">notes</a>
    </body></html>
    """
    assert parse_html_keys(html) == ["202401-citibike-tripdata.zip"]


def test_filter_monthly_archives_limits_to_requested_years():
    keys = [
        "202312-citibike-tripdata.zip",
        "202401-citibike-tripdata.zip",
        "202501-citibike-tripdata.zip",
    ]
    entries = filter_monthly_archives(keys, years=(2024,))
    assert [entry.file_name for entry in entries] == ["202401-citibike-tripdata.zip"]
