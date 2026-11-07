from bigdata_project.manifest import (
    filter_monthly_archives,
    parse_html_keys,
    parse_system_data_page_details,
    parse_system_data_listing_urls,
)


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


def test_parse_system_data_listing_urls_extracts_tripdata_listing():
    html = """
    <html><body>
      <a href="https://s3.amazonaws.com/tripdata/index.html">Trip history</a>
      <a href="/pricing">Pricing</a>
    </body></html>
    """
    assert parse_system_data_listing_urls(html) == ["https://s3.amazonaws.com/tripdata/index.html"]


def test_parse_system_data_page_details_extracts_metadata():
    html = """
    <html>
      <head>
        <meta name="description" content="Trip history landing page" />
      </head>
      <body>
        <h1>System Data</h1>
        <h3>Citi Bike Trip Histories</h3>
        <ul>
          <li>Ride ID</li>
          <li>Rideable type</li>
        </ul>
      </body>
    </html>
    """
    details = parse_system_data_page_details(html)
    assert details["page_title"] == "System Data"
    assert details["page_description"] == "Trip history landing page"
    assert details["trip_history_section_title"] == "Citi Bike Trip Histories"
    assert details["trip_history_fields"] == ["Ride ID", "Rideable type"]
