from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bigdata_project.config import SETTINGS

st.set_page_config(page_title="Citi Bike Analytics", layout="wide")
st.title("Citi Bike Analytics")
st.caption("Dashboard oparty o lokalne wyniki analiz.")


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


monthly = read_csv_if_exists(SETTINGS.outputs_dir / "monthly_trips.csv")
avg_duration = read_csv_if_exists(SETTINGS.outputs_dir / "avg_duration_by_member_type.csv")
bike_share = read_csv_if_exists(SETTINGS.outputs_dir / "bike_type_share.csv")
top_stations = read_csv_if_exists(SETTINGS.outputs_dir / "top_start_stations.csv")

if monthly is None:
    st.warning("Brak wynikow. Najpierw uruchom scripts/run_local_analysis.py.")
    st.stop()

left, right = st.columns(2)

with left:
    # wykres 1: liczba przejazdów w kolejnych miesiącach
    st.subheader("Liczba przejazdow per miesiac")
    monthly["period"] = (
        monthly["trip_year"].astype(str)
        + "-"
        + monthly["trip_month"].astype(str).str.zfill(2)
    )
    st.line_chart(monthly.set_index("period")["ride_count"])

with right:
    # wykres 2: średni czas przejazdu dla każdego typu klienta
    st.subheader("Sredni czas przejazdu per typ klienta (w minutach)")
    if avg_duration is not None:
        avg_duration.columns = ["member_casual", "trip_duration_minutes"]
        st.bar_chart(avg_duration.set_index("member_casual")["trip_duration_minutes"])

lower_left, lower_right = st.columns(2)

with lower_left:
    # wykres 3: liczba przejazdów wg typu roweru
    st.subheader("Udzial typow rowerow")
    if bike_share is not None:
        bike_share.columns = ["rideable_type", "ride_count"]
        st.bar_chart(bike_share.set_index("rideable_type")["ride_count"])

with lower_right:
    # Tabela z 10 najpopularniejszymi stacjami startowymi
    st.subheader("Top stacje startowe")
    if top_stations is not None:
        top_stations.columns = ["start_station_name", "ride_count"]
        st.dataframe(top_stations, use_container_width=True)
