import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Football Econometrics Dashboard", layout="wide")

st.title("Football Econometrics Dashboard")

with st.sidebar:
    season = st.selectbox(
        "Season (end year)",
        options=list(range(2015, 2025)),
        index=9,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def fb_big5_advanced_season_stats(country, gender, season_end_year, tier, stat_type="standard"):
    season_start = season_end_year - 1
    suffix = str(season_end_year)[2:]
    url = f"https://en.wikipedia.org/wiki/{season_start}%E2%80%93{suffix}_Premier_League"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))

    for table in tables:
        cols = list(table.columns)
        has_pos = "Pos" in cols
        has_pts = "Pts" in cols
        team_col = None
        for c in cols:
            if c in ("Team", "Teamvte"):
                team_col = c
                break

        if has_pos and has_pts and team_col:
            df = table[["Pos", team_col, "Pts"]].copy()
            df.columns = ["rk", "squad", "pts"]
            df["squad"] = df["squad"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()
            df["rk"] = pd.to_numeric(df["rk"], errors="coerce").astype("Int64")
            df["pts"] = pd.to_numeric(df["pts"], errors="coerce").astype("Int64")
            df = df.dropna(subset=["rk"])
            df = df.sort_values("rk").reset_index(drop=True)
            return df

    raise ValueError(f"Could not find league table for {season_start}-{season_end_year}")


try:
    with st.spinner("Fetching league data..."):
        league_data = fb_big5_advanced_season_stats(
            "ENG",
            "M",
            int(season),
            "1",
            stat_type="standard",
        )

    st.table(league_data)

except requests.exceptions.HTTPError:
    st.error(f"Could not fetch data for the {season - 1}-{season} season. The page may not be available.")
except Exception as e:
    st.error(f"An error occurred: {e}")
