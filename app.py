import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from io import StringIO
from urllib.parse import quote
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.api as sm
from scipy import stats
import psycopg2
import os
import uuid
import time
from datetime import datetime, timedelta
from models import load_fallback_data, load_fallback_penalty_data

st.set_page_config(page_title="Football Econometrics Dashboard", layout="wide")

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    /* ===== RESPONSIVE LAYOUT ===== */

    /* Mobile phones (up to 768px) */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }

        /* Stack columns vertically on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* Make tables scrollable horizontally */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        .stDataFrame {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        [data-testid="stDataFrame"] table {
            font-size: 0.75rem !important;
        }

        /* Reduce font sizes */
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }

        /* Tabs: scrollable on mobile */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            flex-wrap: nowrap !important;
            gap: 0 !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            white-space: nowrap !important;
            font-size: 0.8rem !important;
            padding: 0.4rem 0.6rem !important;
        }

        /* Sidebar adjustments */
        [data-testid="stSidebar"] {
            min-width: 240px !important;
            max-width: 280px !important;
        }
        [data-testid="stSidebar"] .block-container {
            padding: 0.5rem !important;
        }

        /* Plotly charts responsive */
        .js-plotly-plot, .plotly {
            width: 100% !important;
        }
        .js-plotly-plot .plot-container {
            width: 100% !important;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            padding: 0.3rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }

        /* Expanders */
        [data-testid="stExpander"] summary {
            font-size: 0.9rem !important;
        }
    }

    /* Tablets (769px to 1024px) */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        /* Allow 2 columns on tablet, wrap extras */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }

        /* Tables scrollable */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        .stDataFrame {
            overflow-x: auto !important;
        }

        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.35rem !important; }

        /* Tabs */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-size: 0.85rem !important;
            padding: 0.5rem 0.7rem !important;
        }
    }

    /* Ensure images and charts never overflow */
    img, svg, canvas, video, .js-plotly-plot {
        max-width: 100% !important;
        height: auto !important;
    }

    /* Make all plotly charts responsive */
    .js-plotly-plot .plotly .main-svg {
        width: 100% !important;
    }

    /* Ensure dataframes don't break layout */
    [data-testid="stDataFrame"] > div {
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    /* ===== ANIMATIONS ===== */
    @keyframes slideInUp {
        from { transform: translateY(20px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.5); }
        50%       { box-shadow: 0 0 0 7px rgba(46, 204, 113, 0); }
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes redPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.8; transform: scale(1.06); }
    }

    /* Metric cards slide in on render */
    [data-testid="stMetric"] {
        animation: slideInUp 0.42s ease-out both;
    }

    /* Tab content fades in when switching */
    [data-testid="stTabContent"] > div {
        animation: fadeIn 0.32s ease-in;
    }

    /* Animated gradient insight header */
    .anim-insight-header {
        background: linear-gradient(270deg, #0f2027, #203a43, #2c5364, #1a1a2e, #203a43);
        background-size: 400% 400%;
        animation: gradientShift 10s ease infinite;
        border-radius: 12px;
        padding: 18px 22px;
        margin: 10px 0 14px;
        border-left: 4px solid #00d4ff;
    }

    /* Live season badge */
    .live-badge {
        display: inline-block;
        background: #e74c3c;
        color: #fff;
        font-size: 0.62em;
        font-weight: 800;
        letter-spacing: 0.07em;
        padding: 2px 8px;
        border-radius: 20px;
        animation: redPulse 1.6s ease-in-out infinite;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Complete badge */
    .complete-badge {
        display: inline-block;
        color: #2ecc71;
        font-size: 0.68em;
        font-weight: 700;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Season progress bar */
    .season-progress-wrap {
        background: rgba(255,255,255,0.08);
        border-radius: 8px;
        height: 7px;
        overflow: hidden;
        margin: 5px 0 14px;
    }
    .season-progress-bar {
        height: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #2ecc71, #00d4ff);
        transition: width 1.5s cubic-bezier(0.22, 1, 0.36, 1);
    }

    /* Probability outcome cards */
    .prob-card {
        animation: slideInUp 0.5s ease-out both;
    }
</style>
""", unsafe_allow_html=True)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS page_visits (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            page_name VARCHAR(200) NOT NULL,
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS ai_scout_usage (
            uid VARCHAR(64) PRIMARY KEY,
            week_key VARCHAR(10) NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


init_db()


def record_visit(session_id, page_name):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO page_visits (session_id, page_name) VALUES (%s, %s)",
            (session_id, page_name),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def check_recent_submission(username):
    """Returns True if this username submitted a review in the last hour."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM reviews WHERE LOWER(username) = LOWER(%s) AND created_at >= NOW() - INTERVAL '1 hour'",
            (username,),
        )
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False


def submit_review(username, rating, comment):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reviews (username, rating, comment) VALUES (%s, %s, %s)",
        (username, rating, comment if comment else None),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_good_reviews():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, rating, comment, created_at FROM reviews WHERE rating >= 4 ORDER BY created_at DESC LIMIT 20"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_all_reviews():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, rating, comment, created_at FROM reviews ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_analytics_data():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT session_id) FROM page_visits")
    total_visitors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM page_visits")
    total_views = cur.fetchone()[0]
    cur.execute("""
        SELECT DATE(visited_at) as day, COUNT(DISTINCT session_id) as visitors, COUNT(*) as views
        FROM page_visits
        WHERE visited_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(visited_at)
        ORDER BY day
    """)
    daily_data = cur.fetchall()
    cur.execute("""
        SELECT page_name, COUNT(*) as views
        FROM page_visits
        GROUP BY page_name
        ORDER BY views DESC
    """)
    page_data = cur.fetchall()
    cur.execute("""
        SELECT COUNT(DISTINCT session_id)
        FROM page_visits
        WHERE visited_at >= CURRENT_DATE
    """)
    today_visitors = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(DISTINCT session_id)
        FROM page_visits
        WHERE visited_at >= CURRENT_DATE - INTERVAL '7 days'
    """)
    week_visitors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cur.fetchone()[0]
    cur.execute("SELECT AVG(rating) FROM reviews")
    avg_rating_val = cur.fetchone()[0]
    cur.execute("""
        SELECT rating, COUNT(*) FROM reviews GROUP BY rating ORDER BY rating
    """)
    rating_dist = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "total_visitors": total_visitors,
        "total_views": total_views,
        "daily_data": daily_data,
        "page_data": page_data,
        "today_visitors": today_visitors,
        "week_visitors": week_visitors,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating_val or 0,
        "rating_dist": rating_dist,
    }


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

LEAGUE_CONFIG = {
    "Premier League": {"tm_slug": "premier-league", "tm_code": "GB1", "wiki_pattern": "split", "wiki_name": "Premier_League", "start_year": 1992, "teams": 20, "has_gk_data": True, "season_type": "split", "games_per_season": 38, "is_cup": False, "category": "Europe"},
    "La Liga": {"tm_slug": "laliga", "tm_code": "ES1", "wiki_pattern": "split", "wiki_name": "La_Liga", "start_year": 1992, "teams": 20, "has_gk_data": True, "season_type": "split", "games_per_season": 38, "is_cup": False, "category": "Europe"},
    "Ligue 1": {"tm_slug": "ligue-1", "tm_code": "FR1", "wiki_pattern": "split", "wiki_name": "Ligue_1", "start_year": 1992, "teams": 18, "has_gk_data": True, "season_type": "split", "games_per_season": 34, "is_cup": False, "category": "Europe"},
    "Bundesliga": {"tm_slug": "1-bundesliga", "tm_code": "L1", "wiki_pattern": "split", "wiki_name": "Bundesliga", "start_year": 1992, "teams": 18, "has_gk_data": True, "season_type": "split", "games_per_season": 34, "is_cup": False, "category": "Europe"},
    "Serie A": {"tm_slug": "serie-a", "tm_code": "IT1", "wiki_pattern": "split", "wiki_name": "Serie_A", "start_year": 1992, "teams": 20, "has_gk_data": True, "season_type": "split", "games_per_season": 38, "is_cup": False, "category": "Europe"},
    "Eredivisie": {"tm_slug": "eredivisie", "tm_code": "NL1", "wiki_pattern": "split", "wiki_name": "Eredivisie", "start_year": 1992, "teams": 18, "has_gk_data": True, "season_type": "split", "games_per_season": 34, "is_cup": False, "category": "Europe"},
    "Scottish Premiership": {"tm_slug": "scottish-premiership", "tm_code": "SC1", "wiki_pattern": "split", "wiki_name": "Scottish_Premiership", "start_year": 2013, "teams": 12, "has_gk_data": True, "season_type": "split", "games_per_season": 38, "is_cup": False, "category": "Europe"},
    "Champions League": {"tm_slug": "uefa-champions-league", "tm_code": "CL", "wiki_pattern": None, "wiki_name": None, "start_year": 1992, "teams": 0, "has_gk_data": True, "season_type": "split", "games_per_season": 0, "is_cup": True, "category": "UEFA Competitions"},
    "Europa League": {"tm_slug": "europa-league", "tm_code": "EL", "wiki_pattern": None, "wiki_name": None, "start_year": 2009, "teams": 0, "has_gk_data": True, "season_type": "split", "games_per_season": 0, "is_cup": True, "category": "UEFA Competitions"},
    "Conference League": {"tm_slug": "uefa-europa-conference-league", "tm_code": "UCOL", "wiki_pattern": None, "wiki_name": None, "start_year": 2021, "teams": 0, "has_gk_data": True, "season_type": "split", "games_per_season": 0, "is_cup": True, "category": "UEFA Competitions"},
    "FIFA World Cup": {"tm_slug": "weltmeisterschaft", "tm_code": "WM", "wiki_pattern": None, "wiki_name": None, "start_year": 1930, "teams": 0, "has_gk_data": True, "season_type": "calendar", "games_per_season": 0, "is_cup": True, "category": "International"},
    "UEFA European Championship": {"tm_slug": "europameisterschaft", "tm_code": "EURO", "wiki_pattern": None, "wiki_name": None, "start_year": 1960, "teams": 0, "has_gk_data": True, "season_type": "calendar", "games_per_season": 0, "is_cup": True, "category": "International"},
    "AFC Asian Cup": {"tm_slug": "asienmeisterschaft", "tm_code": "AFC", "wiki_pattern": None, "wiki_name": None, "start_year": 1956, "teams": 0, "has_gk_data": True, "season_type": "calendar", "games_per_season": 0, "is_cup": True, "category": "International"},
    "Copa América": {"tm_slug": "copa-america", "tm_code": "CAM", "wiki_pattern": None, "wiki_name": None, "start_year": 1975, "teams": 0, "has_gk_data": True, "season_type": "calendar", "games_per_season": 0, "is_cup": True, "category": "International"},
    "CONMEBOL Libertadores": {"tm_slug": "copa-libertadores", "tm_code": "CLI", "wiki_pattern": None, "wiki_name": None, "start_year": 1960, "teams": 0, "has_gk_data": True, "season_type": "calendar", "games_per_season": 0, "is_cup": True, "category": "International"},
    "Saudi Pro League": {"tm_slug": "saudi-pro-league", "tm_code": "SA1", "wiki_pattern": "split", "wiki_name": "Saudi_Pro_League", "start_year": 2008, "teams": 18, "has_gk_data": True, "season_type": "split", "games_per_season": 34, "is_cup": False, "category": "Middle East"},
    "Indian Super League": {"tm_slug": "indian-super-league", "tm_code": "IND1", "wiki_pattern": "split", "wiki_name": "Indian_Super_League_season", "start_year": 2014, "teams": 13, "has_gk_data": True, "season_type": "split", "games_per_season": 24, "is_cup": False, "category": "Asia"},
    "J1 League": {"tm_slug": "j1-league", "tm_code": "JAP1", "wiki_pattern": "calendar", "wiki_name": "J1_League", "start_year": 1993, "teams": 20, "has_gk_data": True, "season_type": "calendar", "games_per_season": 38, "is_cup": False, "category": "Asia"},
    "K League 1": {"tm_slug": "k-league-1", "tm_code": "RSK1", "wiki_pattern": "calendar", "wiki_name": "K_League_1", "start_year": 1983, "teams": 12, "has_gk_data": True, "season_type": "calendar", "games_per_season": 38, "is_cup": False, "category": "Asia"},
    "Singapore Premier League": {"tm_slug": "singapore-premier-league", "tm_code": "SIN1", "wiki_pattern": "calendar", "wiki_name": "Singapore_Premier_League", "start_year": 2009, "teams": 8, "has_gk_data": True, "season_type": "calendar", "games_per_season": 21, "is_cup": False, "category": "Asia"},
    "MLS": {"tm_slug": "major-league-soccer", "tm_code": "MLS1", "wiki_pattern": "calendar", "wiki_name": "Major_League_Soccer_season", "start_year": 1996, "teams": 30, "has_gk_data": True, "season_type": "calendar", "games_per_season": 34, "is_cup": False, "category": "Americas"},
    "Argentine Primera División": {"tm_slug": "superliga", "tm_code": "AR1N", "wiki_pattern": "calendar", "wiki_name": "Argentine_Primera_División", "start_year": 2014, "teams": 30, "has_gk_data": False, "season_type": "calendar", "games_per_season": 27, "is_cup": False, "category": "Americas"},
    "Brasileirão Série A": {"tm_slug": "campeonato-brasileiro-serie-a", "tm_code": "BRA1", "wiki_pattern": "calendar", "wiki_name": "Campeonato_Brasileiro_Série_A", "start_year": 2003, "teams": 20, "has_gk_data": True, "season_type": "calendar", "games_per_season": 38, "is_cup": False, "category": "Americas"},
    "Liga BetPlay (Colombia)": {"tm_slug": "liga-betplay-dimayor", "tm_code": "COL1", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 20, "has_gk_data": False, "season_type": "calendar", "games_per_season": 20, "is_cup": False, "category": "Americas"},
    "Chilean Primera División": {"tm_slug": "campeonato-nacional", "tm_code": "CLPD", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 16, "has_gk_data": False, "season_type": "calendar", "games_per_season": 30, "is_cup": False, "category": "Americas"},
    "Uruguayan Primera División": {"tm_slug": "primera-division", "tm_code": "URU1", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 16, "has_gk_data": False, "season_type": "calendar", "games_per_season": 30, "is_cup": False, "category": "Americas"},
    "Paraguayan Primera División": {"tm_slug": "division-de-honor", "tm_code": "PAR1", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 12, "has_gk_data": False, "season_type": "calendar", "games_per_season": 22, "is_cup": False, "category": "Americas"},
    "Peruvian Liga 1": {"tm_slug": "liga-1", "tm_code": "PE1N", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 19, "has_gk_data": False, "season_type": "calendar", "games_per_season": 34, "is_cup": False, "category": "Americas"},
    "Bolivian Primera División": {"tm_slug": "division-profesional", "tm_code": "BOL1", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 16, "has_gk_data": False, "season_type": "calendar", "games_per_season": 30, "is_cup": False, "category": "Americas"},
    "Venezuelan Primera División": {"tm_slug": "primera-division", "tm_code": "VEN1", "wiki_pattern": "calendar", "wiki_name": None, "start_year": 2014, "teams": 18, "has_gk_data": False, "season_type": "calendar", "games_per_season": 34, "is_cup": False, "category": "Americas"},
}


@st.cache_data(ttl=3600, show_spinner=False)
def detect_current_season():
    from datetime import date
    today = date.today()
    if today.month >= 8:
        return today.year + 1
    return today.year


CURRENT_SEASON_END = detect_current_season()

CATEGORY_ORDER = ["Europe", "UEFA Competitions", "International", "Middle East", "Asia", "Americas"]
_categorised = {}
for _name, _cfg in LEAGUE_CONFIG.items():
    _cat = _cfg.get("category", "Other")
    _categorised.setdefault(_cat, []).append(_name)
LEAGUE_OPTIONS = []
for _cat in CATEGORY_ORDER:
    if _cat in _categorised:
        for _name in _categorised[_cat]:
            LEAGUE_OPTIONS.append(_name)

with st.sidebar:
    st.header("Navigation")
    nav_page = st.radio(
        "Go to",
        ["Dashboard", "Analytics", "Feedback", "AI Scout"],
        index=0,
        key="nav_page",
        horizontal=True,
    )
    st.divider()
    st.header("Controls")

    _LEAGUE_ICONS = {
        "Premier League": "\U0001f1ec\U0001f1e7",
        "La Liga": "\U0001f1ea\U0001f1f8",
        "Ligue 1": "\U0001f1eb\U0001f1f7",
        "Bundesliga": "\U0001f1e9\U0001f1ea",
        "Serie A": "\U0001f1ee\U0001f1f9",
        "Eredivisie": "\U0001f1f3\U0001f1f1",
        "Scottish Premiership": "\U0001f1ec\U0001f1e7",
        "Champions League": "\u2b50",
        "Europa League": "\U0001f7e0",
        "Conference League": "\U0001f7e2",
        "FIFA World Cup": "\U0001f3c6",
        "UEFA European Championship": "\U0001f1ea\U0001f1fa",
        "AFC Asian Cup": "\U0001f3c6",
        "Copa Am\u00e9rica": "\U0001f3c6",
        "CONMEBOL Libertadores": "\U0001f3c6",
        "Saudi Pro League": "\U0001f1f8\U0001f1e6",
        "Indian Super League": "\U0001f1ee\U0001f1f3",
        "J1 League": "\U0001f1ef\U0001f1f5",
        "K League 1": "\U0001f1f0\U0001f1f7",
        "Singapore Premier League": "\U0001f1f8\U0001f1ec",
        "MLS": "\U0001f1fa\U0001f1f8",
        "Argentine Primera Divisi\u00f3n": "\U0001f1e6\U0001f1f7",
        "Brasileir\u00e3o S\u00e9rie A": "\U0001f1e7\U0001f1f7",
        "Liga BetPlay (Colombia)": "\U0001f1e8\U0001f1f4",
        "Chilean Primera Divisi\u00f3n": "\U0001f1e8\U0001f1f1",
        "Uruguayan Primera Divisi\u00f3n": "\U0001f1fa\U0001f1fe",
        "Paraguayan Primera Divisi\u00f3n": "\U0001f1f5\U0001f1fe",
        "Peruvian Liga 1": "\U0001f1f5\U0001f1ea",
        "Bolivian Primera Divisi\u00f3n": "\U0001f1e7\U0001f1f4",
        "Venezuelan Primera Divisi\u00f3n": "\U0001f1fb\U0001f1ea",
    }

    def _format_league(name):
        icon = _LEAGUE_ICONS.get(name, "\u26bd")
        return f"{icon} {name}"

    _is_loading = st.session_state.get("_data_loading", False)

    selected_league = st.selectbox("Competition", LEAGUE_OPTIONS, index=0, format_func=_format_league, disabled=_is_loading)
    league_cfg = LEAGUE_CONFIG[selected_league]

    _LOGO_OVERRIDES = {
        "PE1N": "pe1n",
        "COL1": "col1",
        "CLPD": "clpd",
        "URU1": "uru1",
        "PAR1": "par1",
        "BOL1": "bol1",
        "VEN1": "ven1",
    }
    _logo_code = league_cfg["tm_code"]
    _logo_slug = _LOGO_OVERRIDES.get(_logo_code, _logo_code.lower())
    _logo_url = f"https://tmssl.akamaized.net/images/logo/header/{_logo_slug}.png?lm=1"
    st.markdown(
        f'<div style="text-align:center;padding:8px 0;">'
        f'<div style="display:inline-block;background:rgba(255,255,255,0.92);border-radius:50%;padding:14px;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.15);">'
        f'<img src="{_logo_url}" alt="{selected_league}" '
        f'style="max-height:70px;max-width:70px;display:block;" '
        f'onerror="this.onerror=null;this.style.display=\'none\';this.parentElement.innerHTML='
        f'\'<span style=&quot;font-size:40px;&quot;>&#9917;</span>\';">'
        f'</div>'
        f'<div style="font-size:0.85em;color:#888;margin-top:6px;">{selected_league}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    is_tournament = league_cfg.get("is_cup", False)

    if not is_tournament:
        if league_cfg["season_type"] == "split":
            first_season_val = league_cfg["start_year"] + 1
            all_seasons = list(range(first_season_val, CURRENT_SEASON_END + 1))
            season = st.selectbox(
                "Season (end year)",
                options=all_seasons,
                index=len(all_seasons) - 1,
                format_func=lambda y: f"{y - 1}-{str(y)[2:]}",
                disabled=_is_loading,
            )
        else:
            first_season_val = league_cfg["start_year"]
            current_cal = CURRENT_SEASON_END - 1
            all_seasons = list(range(first_season_val, current_cal + 1))
            season = st.selectbox(
                "Season",
                options=all_seasons,
                index=len(all_seasons) - 1,
                disabled=_is_loading,
            )

        st.divider()
        st.subheader("Multi-Season Analysis")
        range_min = first_season_val
        range_max = all_seasons[-1] if all_seasons else first_season_val
        season_range = st.slider(
            "Season range for analysis",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            disabled=_is_loading,
        )
    else:
        if league_cfg["season_type"] == "split":
            first_season_val = league_cfg["start_year"] + 1
        else:
            first_season_val = league_cfg["start_year"]
        all_seasons = []
        season = None
        season_range = (first_season_val, CURRENT_SEASON_END)
        st.info(f"{selected_league} is a cup/tournament competition — only penalty analysis is available.")

if not is_tournament:
    if league_cfg["season_type"] == "split":
        caption_range = f"{league_cfg['start_year']}-{str(league_cfg['start_year'] + 1)[2:]} to {CURRENT_SEASON_END - 1}-{str(CURRENT_SEASON_END)[2:]}"
    else:
        caption_range = f"{league_cfg['start_year']} to {CURRENT_SEASON_END - 1}"
else:
    caption_range = f"{league_cfg['start_year']}-present"


def render_star_display(rating):
    filled = int(rating)
    empty = 5 - filled
    return '<span style="color: #FFD700; font-size: 1.3em;">' + ("&#9733;" * filled) + ("&#9734;" * empty) + "</span>"


if nav_page == "Analytics":
    record_visit(st.session_state.session_id, "Analytics")
    st.title("Web Analytics")
    st.caption("Visitor traffic and usage statistics for this dashboard")

    analytics = get_analytics_data()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Unique Visitors", f"{analytics['total_visitors']:,}")
    with col2:
        st.metric("Total Page Views", f"{analytics['total_views']:,}")
    with col3:
        st.metric("Today's Visitors", f"{analytics['today_visitors']:,}")
    with col4:
        st.metric("This Week's Visitors", f"{analytics['week_visitors']:,}")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Daily Traffic (Last 30 Days)")
        if analytics["daily_data"]:
            daily_df = pd.DataFrame(analytics["daily_data"], columns=["Date", "Visitors", "Page Views"])
            daily_df["Date"] = pd.to_datetime(daily_df["Date"])
            fig_traffic = go.Figure()
            fig_traffic.add_trace(go.Scatter(
                x=daily_df["Date"], y=daily_df["Visitors"],
                mode="lines+markers", name="Unique Visitors",
                line=dict(color="#1f77b4", width=2),
            ))
            fig_traffic.add_trace(go.Scatter(
                x=daily_df["Date"], y=daily_df["Page Views"],
                mode="lines+markers", name="Page Views",
                line=dict(color="#ff7f0e", width=2),
            ))
            fig_traffic.update_layout(
                xaxis_title="Date", yaxis_title="Count",
                template="plotly_dark", height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_traffic, use_container_width=True)
        else:
            st.info("No traffic data yet. Check back later!")

    with col_right:
        st.subheader("Most Visited Pages")
        if analytics["page_data"]:
            page_df = pd.DataFrame(analytics["page_data"], columns=["Page", "Views"])
            fig_pages = px.bar(
                page_df, x="Views", y="Page", orientation="h",
                color="Views", color_continuous_scale="Blues",
                template="plotly_dark",
            )
            fig_pages.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_pages, use_container_width=True)
        else:
            st.info("No page data yet.")

    st.divider()

    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        st.subheader("Review Statistics")
        st.metric("Total Reviews", analytics["total_reviews"])
        if analytics["avg_rating"]:
            avg_r = float(analytics["avg_rating"])
            st.markdown(f"**Average Rating:** {avg_r:.1f} / 5.0 {render_star_display(round(avg_r))}", unsafe_allow_html=True)

    with col_rev2:
        st.subheader("Rating Distribution")
        if analytics["rating_dist"]:
            rd_df = pd.DataFrame(analytics["rating_dist"], columns=["Rating", "Count"])
            rd_df["Rating"] = rd_df["Rating"].apply(lambda r: f"{r} Star{'s' if r > 1 else ''}")
            rating_color_map = {
                "5 Stars": "#2ecc71",
                "4 Stars": "#3498db",
                "3 Stars": "#f1c40f",
                "2 Stars": "#e74c3c",
                "1 Star": "#c0392b",
            }
            fig_rd = px.pie(rd_df, values="Count", names="Rating", template="plotly_dark",
                           color_discrete_map=rating_color_map)
            fig_rd.update_layout(height=300, showlegend=True,
                                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02))
            fig_rd.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_rd, use_container_width=True)
        else:
            st.info("No reviews yet.")

    st.stop()

if nav_page == "Feedback":
    record_visit(st.session_state.session_id, "Feedback")
    st.title("Feedback Dashboard")
    st.caption("Share your thoughts and see what others are saying about the Football Econometrics Dashboard")

    if "show_goal_animation" not in st.session_state:
        st.session_state.show_goal_animation = False

    if st.session_state.show_goal_animation:
        st.markdown("""
        <div id="goal-animation-overlay" style="
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.85); z-index: 9999;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            animation: fadeInOverlay 0.3s ease-in;
        ">
            <style>
                @keyframes fadeInOverlay { from { opacity: 0; } to { opacity: 1; } }
                @keyframes ballKick {
                    0% { transform: translate(0, 200px) scale(1); opacity: 1; }
                    40% { transform: translate(0, -20px) scale(1.3); opacity: 1; }
                    60% { transform: translate(0, -40px) scale(1.1); opacity: 1; }
                    100% { transform: translate(0, -60px) scale(1); opacity: 1; }
                }
                @keyframes netShake {
                    0%, 100% { transform: scaleX(1); }
                    25% { transform: scaleX(1.03); }
                    50% { transform: scaleX(0.97); }
                    75% { transform: scaleX(1.02); }
                }
                @keyframes goalTextPop {
                    0% { transform: scale(0); opacity: 0; }
                    50% { transform: scale(1.3); opacity: 1; }
                    70% { transform: scale(0.9); }
                    100% { transform: scale(1); opacity: 1; }
                }
                @keyframes confettiFall {
                    0% { transform: translateY(-10px) rotate(0deg); opacity: 1; }
                    100% { transform: translateY(400px) rotate(720deg); opacity: 0; }
                }
                .confetti-piece {
                    position: absolute; width: 10px; height: 10px; top: 80px;
                    animation: confettiFall 2.5s ease-in forwards;
                }
            </style>
            <svg width="320" height="220" viewBox="0 0 320 220" style="animation: netShake 0.5s ease-in-out 0.6s 3;">
                <rect x="40" y="20" width="240" height="160" rx="5" fill="none" stroke="white" stroke-width="4"/>
                <line x1="40" y1="60" x2="280" y2="60" stroke="white" stroke-width="1" opacity="0.4"/>
                <line x1="40" y1="100" x2="280" y2="100" stroke="white" stroke-width="1" opacity="0.4"/>
                <line x1="40" y1="140" x2="280" y2="140" stroke="white" stroke-width="1" opacity="0.4"/>
                <line x1="120" y1="20" x2="120" y2="180" stroke="white" stroke-width="1" opacity="0.4"/>
                <line x1="200" y1="20" x2="200" y2="180" stroke="white" stroke-width="1" opacity="0.4"/>
                <rect x="40" y="20" width="240" height="160" rx="5" fill="rgba(255,255,255,0.05)"/>
                <circle cx="160" cy="130" r="22" fill="white" stroke="#333" stroke-width="2"
                        style="animation: ballKick 0.8s ease-out forwards;">
                    <animate attributeName="cy" from="200" to="100" dur="0.7s" fill="freeze"/>
                </circle>
                <path d="M160 108 L148 118 L152 132 L168 132 L172 118 Z" fill="#333" opacity="0.8">
                    <animate attributeName="opacity" from="0" to="0.8" dur="0.7s" fill="freeze"/>
                </path>
            </svg>
            <div style="animation: goalTextPop 0.6s ease-out 0.5s both;">
                <h1 style="color: #2ecc71; font-size: 3em; margin: 10px 0; text-shadow: 0 0 30px rgba(46,204,113,0.5);">
                    GOAL!
                </h1>
            </div>
            <div style="animation: goalTextPop 0.6s ease-out 0.8s both;">
                <p style="color: white; font-size: 1.4em; margin: 0;">Feedback Submitted Successfully!</p>
            </div>
            <div style="animation: goalTextPop 0.5s ease-out 1.2s both;">
                <p style="color: #aaa; font-size: 1em; margin-top: 5px;">Thank you for helping us improve ⚽</p>
            </div>
            <div class="confetti-piece" style="left:15%; background:#2ecc71; animation-delay:0.5s; border-radius:50%;"></div>
            <div class="confetti-piece" style="left:25%; background:#f1c40f; animation-delay:0.7s;"></div>
            <div class="confetti-piece" style="left:35%; background:#e74c3c; animation-delay:0.6s; border-radius:50%;"></div>
            <div class="confetti-piece" style="left:45%; background:#3498db; animation-delay:0.8s;"></div>
            <div class="confetti-piece" style="left:55%; background:#2ecc71; animation-delay:0.5s;"></div>
            <div class="confetti-piece" style="left:65%; background:#f1c40f; animation-delay:0.9s; border-radius:50%;"></div>
            <div class="confetti-piece" style="left:75%; background:#e74c3c; animation-delay:0.7s;"></div>
            <div class="confetti-piece" style="left:85%; background:#3498db; animation-delay:0.6s; border-radius:50%;"></div>
            <script>
                setTimeout(function() {
                    var overlay = document.getElementById('goal-animation-overlay');
                    if (overlay) {
                        overlay.style.transition = 'opacity 0.5s';
                        overlay.style.opacity = '0';
                        setTimeout(function() { overlay.remove(); }, 500);
                    }
                }, 3500);
            </script>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.show_goal_animation = False

    st.subheader("Submit Your Feedback")
    st.caption("Your feedback helps us improve. Leave a rating and an optional comment.")

    with st.form("feedback_form_page", clear_on_submit=True):
        fb_cols = st.columns([1, 1, 2])
        with fb_cols[0]:
            fb_username = st.text_input("Your name", max_chars=100, placeholder="e.g. FootballFan99")
        with fb_cols[1]:
            fb_rating = st.select_slider(
                "Rating",
                options=[1, 2, 3, 4, 5],
                value=5,
                format_func=lambda x: "\u2605" * x + "\u2606" * (5 - x),
            )
        with fb_cols[2]:
            fb_comment = st.text_area("Comment (optional)", max_chars=500, placeholder="What did you like? Any suggestions?", height=80)

        submitted = st.form_submit_button("Submit Review", type="primary", use_container_width=True)
        if submitted:
            if not fb_username or not fb_username.strip():
                st.error("Please enter your name.")
            else:
                _now = datetime.now()
                _last_submit = st.session_state.get("_last_feedback_submit")
                _cooldown_secs = 60
                if _last_submit is not None and (_now - _last_submit).total_seconds() < _cooldown_secs:
                    _wait = int(_cooldown_secs - (_now - _last_submit).total_seconds())
                    st.warning(f"You just submitted a review. Please wait {_wait} second{'s' if _wait != 1 else ''} before submitting again.")
                elif check_recent_submission(fb_username.strip()):
                    st.warning(
                        f"A review from **{fb_username.strip()}** was already submitted in the last hour. "
                        "Please wait before submitting another, or use a different name."
                    )
                else:
                    try:
                        submit_review(fb_username.strip(), fb_rating, fb_comment.strip() if fb_comment else None)
                        st.session_state["_last_feedback_submit"] = _now
                        st.session_state.show_goal_animation = True
                        st.rerun()
                    except Exception as ex:
                        st.error("Could not save your review. Please try again.")

    st.divider()

    all_reviews = get_all_reviews()

    rev_col1, rev_col2, rev_col3 = st.columns(3)
    total_count = len(all_reviews)
    avg_rating_fb = sum(r[1] for r in all_reviews) / total_count if total_count > 0 else 0
    five_star_count = sum(1 for r in all_reviews if r[1] == 5)
    with rev_col1:
        st.metric("Total Reviews", total_count)
    with rev_col2:
        if total_count > 0:
            st.metric("Average Rating", f"{avg_rating_fb:.1f} / 5.0")
        else:
            st.metric("Average Rating", "N/A")
    with rev_col3:
        st.metric("5-Star Reviews", five_star_count)

    if total_count > 0:
        st.divider()
        rating_counts = {}
        for r in all_reviews:
            rating_counts[r[1]] = rating_counts.get(r[1], 0) + 1
        rc_col1, rc_col2 = st.columns(2)
        with rc_col1:
            st.subheader("Rating Distribution")
            rd_data = []
            for star in range(5, 0, -1):
                count = rating_counts.get(star, 0)
                pct = (count / total_count * 100) if total_count > 0 else 0
                rd_data.append({"Rating": f"{star} Star{'s' if star > 1 else ''}", "Count": count, "Percentage": pct})
            rd_df = pd.DataFrame(rd_data)
            rating_colors = {"5 Stars": "#2ecc71", "4 Stars": "#3498db", "3 Stars": "#f1c40f", "2 Stars": "#e74c3c", "1 Star": "#c0392b"}
            fig_rd = px.bar(rd_df, x="Count", y="Rating", orientation="h", template="plotly_dark",
                           color="Rating", color_discrete_map=rating_colors)
            fig_rd.update_layout(height=250, showlegend=False, yaxis=dict(categoryorder="array", categoryarray=[f"{s} Star{'s' if s > 1 else ''}" for s in range(5, 0, -1)]))
            st.plotly_chart(fig_rd, use_container_width=True)

        with rc_col2:
            st.subheader("Sentiment Breakdown")
            positive = sum(1 for r in all_reviews if r[1] >= 4)
            neutral = sum(1 for r in all_reviews if r[1] == 3)
            negative = sum(1 for r in all_reviews if r[1] <= 2)
            sent_df = pd.DataFrame({"Sentiment": ["Positive (4-5)", "Neutral (3)", "Negative (1-2)"], "Count": [positive, neutral, negative]})
            sent_colors = {"Positive (4-5)": "#2ecc71", "Neutral (3)": "#f1c40f", "Negative (1-2)": "#e74c3c"}
            fig_sent = px.pie(sent_df, values="Count", names="Sentiment", template="plotly_dark",
                             color="Sentiment", color_discrete_map=sent_colors)
            fig_sent.update_layout(height=250)
            fig_sent.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_sent, use_container_width=True)

        st.divider()
        st.subheader("All Reviews")

        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            filter_rating = st.selectbox("Filter by rating", ["All", "5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"])

        filtered_reviews = all_reviews
        if filter_rating != "All":
            filter_val = int(filter_rating[0])
            filtered_reviews = [r for r in all_reviews if r[1] == filter_val]

        if filtered_reviews:
            st.caption(f"Showing {len(filtered_reviews)} review{'s' if len(filtered_reviews) != 1 else ''}")
            for username, rating, comment, created_at in filtered_reviews:
                with st.container():
                    r_cols = st.columns([1, 3, 1])
                    with r_cols[0]:
                        st.markdown(f"**{username}**")
                        st.markdown(render_star_display(rating), unsafe_allow_html=True)
                    with r_cols[1]:
                        if comment:
                            st.markdown(f'"{comment}"')
                        else:
                            st.markdown("*No comment*", help="This user did not leave a comment")
                    with r_cols[2]:
                        st.caption(created_at.strftime("%b %d, %Y") if hasattr(created_at, 'strftime') else str(created_at))
                    st.markdown("---")
        else:
            st.info("No reviews match the selected filter.")
    else:
        st.info("No reviews yet. Be the first to leave feedback!")

    st.stop()

# ── AI Scout ─────────────────────────────────────────────────────────────────
if nav_page == "AI Scout":
    import base64
    import openai

    record_visit(st.session_state.session_id, "AI Scout")

    _WEEKLY_LIMIT = 30

    # ── Persistent UID via URL query param (survives refresh) ────────────────
    _uid = st.query_params.get("uid", None)
    if not _uid:
        _uid = str(uuid.uuid4())
        st.query_params["uid"] = _uid

    # ── Week key: ISO week (Mon–Sun), UTC ────────────────────────────────────
    def _current_week_key():
        now_utc = datetime.utcnow()
        iso = now_utc.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"

    # ── DB helpers ───────────────────────────────────────────────────────────
    def _get_scout_usage(uid):
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT week_key, count FROM ai_scout_usage WHERE uid = %s", (uid,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return row[0], row[1]
        except Exception:
            pass
        return _current_week_key(), 0

    def _increment_scout_usage(uid, week_key):
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ai_scout_usage (uid, week_key, count, updated_at)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (uid) DO UPDATE SET
                    count = CASE
                        WHEN ai_scout_usage.week_key = EXCLUDED.week_key
                        THEN ai_scout_usage.count + 1
                        ELSE 1
                    END,
                    week_key = EXCLUDED.week_key,
                    updated_at = NOW()
                """,
                (uid, week_key),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass

    def _friendly_ai_error(exc):
        msg = str(exc).lower()
        if "connection" in msg or "timeout" in msg or "unreachable" in msg or "name or service not known" in msg:
            return (
                "The AI service is temporarily unreachable — this is usually a brief network hiccup. "
                "Please wait a moment and try again."
            )
        if "429" in msg or "rate_limit" in msg or "rate limit" in msg or "too many requests" in msg:
            return (
                "The AI service is very busy right now. Please wait a few seconds and try again — "
                "your message has not been counted against your weekly limit."
            )
        if "502" in msg or "503" in msg or "500" in msg or "bad gateway" in msg or "service unavailable" in msg:
            return (
                "The AI service is experiencing a temporary issue on our end. "
                "Please try again in a minute."
            )
        if "401" in msg or "403" in msg or "unauthorized" in msg or "forbidden" in msg:
            return "There's an authentication issue with the AI service. Please contact the dashboard owner."
        if "model" in msg and ("not found" in msg or "does not exist" in msg):
            return "The AI model is currently unavailable. Please try again later."
        return (
            "Something went wrong when reaching the AI. "
            "Please try your question again — if the problem persists, come back in a few minutes."
        )

    def _search_football_context(query, max_snippets=8):
        """Search the web for recent football context. Returns list of dicts with title/snippet/url."""
        try:
            from urllib.parse import quote as _quote, unquote as _unquote
            yr = datetime.utcnow().year
            search_q = _quote(f"{query} {yr}")
            search_url = f"https://html.duckduckgo.com/html/?q={search_q}"
            hdrs = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-GB,en;q=0.9",
            }
            resp = requests.get(search_url, headers=hdrs, timeout=8)
            soup_s = BeautifulSoup(resp.text, "html.parser")
            results = []
            for result in soup_s.select(".result")[:max_snippets]:
                title_el = result.select_one(".result__title")
                snip_el  = result.select_one(".result__snippet")
                url_el   = result.select_one(".result__url")
                # Try to get the real URL from the title link
                link_el  = result.select_one(".result__title a")
                href = ""
                if link_el and link_el.get("href"):
                    raw = link_el["href"]
                    # DuckDuckGo wraps urls as /l/?uddg=<encoded_url>
                    if "uddg=" in raw:
                        try:
                            href = _unquote(raw.split("uddg=")[1].split("&")[0])
                        except Exception:
                            href = ""
                    elif raw.startswith("http"):
                        href = raw
                displayed_url = url_el.get_text(strip=True) if url_el else href
                title = title_el.get_text(separator=" ", strip=True) if title_el else ""
                snip  = snip_el.get_text(separator=" ", strip=True)  if snip_el  else ""
                if snip:
                    results.append({
                        "title": title,
                        "snippet": snip,
                        "url": href or displayed_url,
                        "source": displayed_url or href,
                    })
            return results
        except Exception:
            return []

    # ── Usage check ──────────────────────────────────────────────────────────
    _week_key = _current_week_key()
    _stored_week, _used_count = _get_scout_usage(_uid)
    if _stored_week != _week_key:
        _used_count = 0
    _remaining = max(0, _WEEKLY_LIMIT - _used_count)

    # ── OpenAI client ────────────────────────────────────────────────────────
    _BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    _API_KEY  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
    _MODEL    = "gpt-4.1"

    if not _BASE_URL or not _API_KEY:
        st.error("The AI service is not currently configured. Please check back later.")
        st.stop()

    _client = openai.OpenAI(base_url=_BASE_URL, api_key=_API_KEY)

    if "ai_scout_messages" not in st.session_state:
        st.session_state.ai_scout_messages = []
    if "scout_image_data" not in st.session_state:
        st.session_state.scout_image_data = None  # (bytes, mime) tuple or None

    # ── CSS: compact uploader + scroll-to-top + bottom-left upload bar ───────
    st.markdown("""
    <style>
    /* Scroll-to-top: fixed top-right */
    #scout-scroll-top {
        position: fixed; top: 70px; right: 18px; z-index: 9999;
    }
    #scout-scroll-top button {
        background: #1565C0; color: white; border: none; border-radius: 50%;
        width: 36px; height: 36px; font-size: 15px; cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }

    /* Hide only the visual clutter inside the dropzone (SVG, "Drag and drop"
       text, file-size note) — but KEEP the Browse button so uploads work */
    [data-testid="stFileUploaderDropzone"] > div:first-child { display: none !important; }
    [data-testid="stFileUploaderDropzone"] > span         { display: none !important; }
    [data-testid="stFileUploaderDropzone"] > small        { display: none !important; }
    [data-testid="stFileUploaderDropzone"] {
        padding: 0 !important; border: none !important;
        background: transparent !important; min-height: 0 !important;
    }
    /* Hide the outer label too */
    div[data-testid="stFileUploader"] > label { display: none !important; }
    div[data-testid="stFileUploader"] section { padding: 0 !important; }

    /* Position the file uploader fixed at bottom-left, above the chat bar */
    div[data-testid="stFileUploader"] {
        position: fixed !important;
        bottom: 72px !important;
        left: 14px !important;
        z-index: 1000 !important;
        width: auto !important;
        background: transparent !important;
    }
    </style>
    <div id="scout-scroll-top">
      <button onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Scroll to top">&#8679;</button>
    </div>
    """, unsafe_allow_html=True)

    # ── Page header ──────────────────────────────────────────────────────────
    st.title("AI Football Scout")
    st.caption(
        "Ask anything about football stats, tactics, or econometrics — "
        "or attach an image (📎) to let the AI analyse a screenshot."
    )

    if _remaining > 0:
        st.info(
            f"You have **{_remaining} of {_WEEKLY_LIMIT} messages** left this week. "
            "Your allowance resets every **Sunday at 23:59 GMT**."
        )
    else:
        st.warning(
            f"You've used all **{_WEEKLY_LIMIT} messages**  for this week. "
            "Your allowance resets every **Sunday at 23:59 GMT** — come back then!"
        )

    # ── Clear button (top of chat area) ───────────────────────────────────────
    if st.button("🗑️ Clear chat", key="scout_clear", help="Clear conversation"):
        st.session_state.ai_scout_messages = []
        st.session_state.scout_image_data = None
        st.rerun()

    # ── Image status banner ───────────────────────────────────────────────────
    if st.session_state.scout_image_data:
        st.caption("📎 Image attached — will be sent with your next message.")

    # ── File uploader — CSS positions it fixed at bottom-left ────────────────
    uploaded_image = st.file_uploader(
        "📎 Attach image", type=["png", "jpg", "jpeg", "webp"],
        key="scout_image", label_visibility="collapsed",
        help="Attach a screenshot for the AI to analyse",
    )

    # Persist image bytes in session so it survives reruns
    if uploaded_image is not None:
        uploaded_image.seek(0)
        st.session_state.scout_image_data = (uploaded_image.read(), uploaded_image.type or "image/png")

    # ── Message history (full width) ─────────────────────────────────────────
    for msg in st.session_state.ai_scout_messages:
        with st.chat_message(msg["role"]):
            if msg.get("image_b64"):
                st.image(
                    base64.b64decode(msg["image_b64"]),
                    width=280,
                    caption="Attached image",
                )
            st.markdown(msg["content"])

    # ── Chat input — main level so it sticks to the bottom ───────────────────
    if _remaining > 0:
        user_input = st.chat_input("Ask about stats, tactics, results, models…")
    else:
        user_input = None
        st.chat_input("Weekly limit reached — resets Sunday 23:59 GMT", disabled=True)

    if user_input:
        img_data = st.session_state.scout_image_data  # (bytes, mime) or None

        with st.chat_message("user"):
            if img_data:
                st.image(img_data[0], width=280, caption="Attached image")
            st.markdown(user_input)

        # Build API user content
        if img_data:
            b64_img = base64.b64encode(img_data[0]).decode("utf-8")
            user_content = [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": f"data:{img_data[1]};base64,{b64_img}"}},
            ]
        else:
            b64_img = None
            user_content = user_input

        # Store in history (include image b64 for display on rerun)
        st.session_state.ai_scout_messages.append({
            "role": "user",
            "content": user_input,
            "image_b64": b64_img,
        })
        # Clear attached image after sending
        st.session_state.scout_image_data = None

        with st.chat_message("assistant"):
            # Step 1: fetch live web context
            with st.spinner("Searching for recent updates…"):
                web_snippets = _search_football_context(user_input)

            # Step 2: build dynamic system prompt (date + web context)
            _today_str = datetime.utcnow().strftime("%B %d, %Y")
            dynamic_system = (
                "You are an expert football (soccer) analyst and econometrics tutor "
                "embedded inside a Football Econometrics Dashboard covering 30 competitions worldwide.\n"
                f"Today's date is {_today_str}.\n"
                "IMPORTANT: Your training data has a knowledge cutoff and may be out of date. "
                "Recent web search results are provided below — you MUST treat these as the ground truth "
                "for any facts about current seasons, player transfers, managerial appointments, "
                "league standings, or match results. If the web results contradict your training memory, "
                "always defer to the web results. If you are uncertain about a recent fact and the web "
                "results don't confirm it, say so clearly rather than confidently stating outdated information.\n"
                "Explain concepts in plain, conversational English. Be precise when the user wants detail. "
                "When an image is attached, describe what you see and provide relevant football insights.\n"
                "SOURCE CITATION RULE: At the end of every reply that uses web search results, you MUST include "
                "a 'Sources' section listing every source you drew on. Use this exact format:\n"
                "**Sources**\n"
                "1. [Title or site name](URL)\n"
                "2. [Title or site name](URL)\n"
                "List ALL sources that provided information used in your answer, not just one or two. "
                "If no web results were available, omit the Sources section entirely."
            )
            if web_snippets:
                dynamic_system += "\n\n=== RECENT WEB SEARCH RESULTS (treat as ground truth) ===\n"
                for i, s in enumerate(web_snippets, 1):
                    title   = s.get("title", "")
                    snippet = s.get("snippet", "")
                    url     = s.get("url", "")
                    label   = f"[{title}]" if title else ""
                    src     = f" ({url})" if url else ""
                    dynamic_system += f"{i}. {label}{src}: {snippet}\n"
                dynamic_system += "=== END OF WEB RESULTS ===\n"
                dynamic_system += (
                    "You used the above web results. At the end of your reply you MUST list every source "
                    "that contributed to your answer under a '**Sources**' heading with numbered clickable links."
                )

            api_messages = [{"role": "system", "content": dynamic_system}]
            for prev in st.session_state.ai_scout_messages[:-1]:
                api_messages.append({"role": prev["role"], "content": prev["content"]})
            api_messages.append({"role": "user", "content": user_content})

            # Step 3: call the AI
            with st.spinner("Thinking…"):
                try:
                    response = _client.chat.completions.create(
                        model=_MODEL,
                        messages=api_messages,
                        max_completion_tokens=1024,
                    )
                    reply = response.choices[0].message.content
                    _increment_scout_usage(_uid, _week_key)
                except Exception as exc:
                    reply = _friendly_ai_error(exc)
            st.markdown(reply)

        st.session_state.ai_scout_messages.append({"role": "assistant", "content": reply})

    st.stop()

record_visit(st.session_state.session_id, f"Dashboard - {selected_league}")

st.title("Football Econometrics Dashboard")
st.caption(f"A reproducible econometrics study of what statistically matters for success in the {selected_league} ({caption_range})")

good_reviews = get_good_reviews()
if good_reviews:
    st.markdown("---")
    st.subheader("What Our Users Say")
    review_cols = st.columns(min(len(good_reviews), 4))
    for i, (username, rating, comment, created_at) in enumerate(good_reviews[:4]):
        with review_cols[i % len(review_cols)]:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); '
                f'border-radius: 12px; padding: 18px; margin-bottom: 10px; '
                f'border-left: 4px solid #FFD700;">'
                f'{render_star_display(rating)}<br>'
                f'<span style="color: #ddd; font-style: italic;">'
                f'{"&ldquo;" + comment + "&rdquo;" if comment else "<em>No comment</em>"}</span><br>'
                f'<span style="color: #888; font-size: 0.85em;">— <strong>{username}</strong> '
                f'&middot; {created_at.strftime("%b %d, %Y") if created_at else ""}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    if len(good_reviews) > 4:
        with st.expander(f"View all {len(good_reviews)} reviews"):
            for username, rating, comment, created_at in good_reviews[4:]:
                st.markdown(
                    f'{render_star_display(rating)} **{username}** — '
                    f'{"_" + comment + "_" if comment else "No comment"} '
                    f'({created_at.strftime("%b %d, %Y") if created_at else ""})',
                    unsafe_allow_html=True,
                )
    st.markdown("---")


def share_table_buttons(df, label, key_prefix):
    csv_data = df.to_csv(index=False)
    st.download_button(
        label=f"Download {label} as CSV",
        data=csv_data,
        file_name=f"{label.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key=f"dl_{key_prefix}",
    )


def format_season_label(yr, season_type):
    if season_type == "split":
        return f"{yr - 1}-{str(yr)[2:]}"
    return str(yr)


def _requests_get_with_retry(url, headers, timeout=30, retries=3, backoff=2.0):
    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (429, 503, 502):
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(backoff * (2 ** attempt))
            else:
                raise
    raise last_exc


@st.cache_data(ttl=604800, show_spinner=False)
def fetch_season_data(season_val, wiki_pattern, wiki_name, season_type):
    if wiki_pattern is None or wiki_name is None:
        raise ValueError("League tables are not available for this competition.")

    encoded_name = quote(wiki_name, safe="_")
    if wiki_pattern == "split":
        season_start = season_val - 1
        suffix = str(season_val)[2:]
        url = f"https://en.wikipedia.org/wiki/{season_start}%E2%80%93{suffix}_{encoded_name}"
    else:
        url = f"https://en.wikipedia.org/wiki/{season_val}_{encoded_name}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = _requests_get_with_retry(url, headers)

    tables = pd.read_html(StringIO(response.text))

    for table in tables:
        cols = list(table.columns)
        has_pos = "Pos" in cols
        has_pts = "Pts" in cols
        team_col = None
        for c in cols:
            if c in ("Team", "Teamvte", "Club", "Clubvte", "Squad"):
                team_col = c
                break

        if has_pos and has_pts and team_col:
            pld_col = None
            for candidate in ("Pld", "MP", "P"):
                if candidate in cols:
                    pld_col = candidate
                    break

            wanted = ["Pos", team_col, pld_col, "W", "D", "L", "GF", "GA", "GD", "Pts"]
            wanted = [c for c in wanted if c is not None]
            available = [c for c in wanted if c in cols]
            df = table[available].copy()

            rename_map = {team_col: "Squad"}
            if pld_col and pld_col != "Pld":
                rename_map[pld_col] = "Pld"
            df = df.rename(columns=rename_map)

            df["Squad"] = df["Squad"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()

            for col in ["Pos", "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace("\u2212", "-", regex=False)
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["Pos"])
            df["Pos"] = df["Pos"].astype(int)
            df = df.sort_values("Pos").reset_index(drop=True)
            df["Season"] = format_season_label(season_val, season_type)
            df["Season_End"] = season_val

            if "W" in df.columns and "D" in df.columns:
                df["Pts"] = df["W"] * 3 + df["D"] * 1
            if "Pld" in df.columns and "Pts" in df.columns:
                df["PPG"] = (df["Pts"] / df["Pld"]).round(2)
            if "Pld" in df.columns and "W" in df.columns:
                df["Win%"] = ((df["W"] / df["Pld"]) * 100).round(1)
            if "Pld" in df.columns and "GF" in df.columns:
                df["GF/Game"] = (df["GF"] / df["Pld"]).round(2)
            if "Pld" in df.columns and "GA" in df.columns:
                df["GA/Game"] = (df["GA"] / df["Pld"]).round(2)

            return df

    raise ValueError(f"Could not find league table for season {season_val}")


@st.cache_data(ttl=604800, show_spinner=False)
def load_multi_season(start_year, end_year, wiki_pattern, wiki_name, season_type):
    frames = []
    failed_years = []
    for yr in range(start_year, end_year + 1):
        try:
            df = fetch_season_data(yr, wiki_pattern, wiki_name, season_type)
            frames.append(df)
        except Exception as _ye:
            err = str(_ye).lower()
            if "404" not in err:
                failed_years.append(yr)
    if frames:
        return pd.concat(frames, ignore_index=True), failed_years
    return pd.DataFrame(), failed_years


@st.cache_data(ttl=3600, show_spinner=False)
def load_cross_league_comparison():
    leagues_with_wiki = {
        name: cfg for name, cfg in LEAGUE_CONFIG.items()
        if cfg.get("wiki_pattern") is not None and cfg.get("wiki_name") is not None and not cfg.get("is_cup", False)
    }

    rows = []
    failed_leagues = []
    for league_name, cfg in leagues_with_wiki.items():
        try:
            if cfg["season_type"] == "split":
                season_val = CURRENT_SEASON_END
            else:
                season_val = CURRENT_SEASON_END - 1

            df = fetch_season_data(season_val, cfg["wiki_pattern"], cfg["wiki_name"], cfg["season_type"])
            if df.empty or "GF" not in df.columns or "GA" not in df.columns:
                continue

            gps = cfg["games_per_season"]
            total_teams = len(df)
            total_goals_for = df["GF"].sum()
            total_goals_against = df["GA"].sum()
            total_matches = df["Pld"].sum() / 2 if "Pld" in df.columns else (total_teams * gps) / 2
            total_goals = total_goals_for
            goals_per_match = total_goals / total_matches if total_matches > 0 else 0

            avg_ga = df["GA"].mean()
            best_defence_ga = df["GA"].min()
            best_defence_team = df.loc[df["GA"].idxmin(), "Squad"] if "Squad" in df.columns else ""
            worst_defence_ga = df["GA"].max()
            worst_defence_team = df.loc[df["GA"].idxmax(), "Squad"] if "Squad" in df.columns else ""

            pts_col = df["Pts"] if "Pts" in df.columns else None
            if pts_col is not None:
                pts_std = pts_col.std()
                pts_range = pts_col.max() - pts_col.min()
                leader_pts = pts_col.max()
                bottom_pts = pts_col.min()
            else:
                pts_std = 0
                pts_range = 0
                leader_pts = 0
                bottom_pts = 0

            wins = df["W"].sum() if "W" in df.columns else 0
            draws = df["D"].sum() if "D" in df.columns else 0
            losses = df["L"].sum() if "L" in df.columns else 0
            total_results = wins + draws + losses
            draw_pct = (draws / total_results * 100) if total_results > 0 else 0

            gd_values = df["GD"] if "GD" in df.columns else (df["GF"] - df["GA"])
            avg_gd_spread = gd_values.std() if len(gd_values) > 1 else 0

            games_played = df["Pld"].max() if "Pld" in df.columns else gps
            season_progress = (games_played / gps * 100) if gps > 0 else 100

            rows.append({
                "League": league_name,
                "Teams": total_teams,
                "Goals/Match": round(goals_per_match, 2),
                "Avg GA": round(avg_ga, 1),
                "Best Defence": f"{best_defence_team} ({best_defence_ga:.0f})",
                "Best Defence GA": best_defence_ga,
                "Worst Defence": f"{worst_defence_team} ({worst_defence_ga:.0f})",
                "Draw %": round(draw_pct, 1),
                "Pts Spread": round(pts_range, 0),
                "Competitiveness": round(pts_std, 1),
                "Leader Pts": leader_pts,
                "Bottom Pts": bottom_pts,
                "Season Progress %": round(season_progress, 0),
                "Category": cfg.get("category", "Other"),
            })
        except Exception:
            failed_leagues.append(league_name)
            continue

    result = pd.DataFrame(rows) if rows else pd.DataFrame()
    result.attrs["failed_leagues"] = failed_leagues
    result.attrs["total_leagues"] = len(leagues_with_wiki)
    return result


def rebase_to_standard_season(df, games_per_season):
    if df.empty or games_per_season <= 0 or "Pld" not in df.columns:
        return df
    result = df.copy()
    result["Rebased"] = False
    result["Original_Pld"] = result["Pld"]
    if "Season_End" in result.columns:
        for se in result["Season_End"].unique():
            mask = result["Season_End"] == se
            season_pld = result.loc[mask, "Pld"]
            mode_pld = int(season_pld.mode().iloc[0]) if not season_pld.mode().empty else int(season_pld.max())
            if mode_pld == games_per_season:
                continue
            is_complete = (season_pld == mode_pld).all()
            if not is_complete:
                continue
            scale = games_per_season / mode_pld
            counting_cols = ["Pts", "W", "D", "L", "GF", "GA", "GD"]
            for col in counting_cols:
                if col in result.columns:
                    result.loc[mask, col] = (result.loc[mask, col] * scale).round(0).astype(int)
            result.loc[mask, "Pld"] = games_per_season
            result.loc[mask, "Rebased"] = True
    else:
        mode_pld = int(result["Pld"].mode().iloc[0]) if not result["Pld"].mode().empty else int(result["Pld"].max())
        mode_share = (result["Pld"] == mode_pld).sum() / len(result)
        if mode_pld != games_per_season and mode_share >= 0.9:
            mask = result["Pld"] == mode_pld
            scale = games_per_season / mode_pld
            counting_cols = ["Pts", "W", "D", "L", "GF", "GA", "GD"]
            for col in counting_cols:
                if col in result.columns:
                    result.loc[mask, col] = (result.loc[mask, col] * scale).round(0).astype(int)
            result.loc[mask, "Pld"] = games_per_season
            result.loc[mask, "Rebased"] = True
    if "PPG" in result.columns and "Pts" in result.columns:
        result["PPG"] = (result["Pts"] / result["Pld"]).round(2)
    if "Win%" in result.columns and "W" in result.columns:
        result["Win%"] = ((result["W"] / result["Pld"]) * 100).round(1)
    if "GF/Game" in result.columns and "GF" in result.columns:
        result["GF/Game"] = (result["GF"] / result["Pld"]).round(2)
    if "GA/Game" in result.columns and "GA" in result.columns:
        result["GA/Game"] = (result["GA"] / result["Pld"]).round(2)
    return result


@st.cache_data(ttl=604800, show_spinner=False)
def scrape_penalty_takers(tm_slug, tm_code, season_id=None, is_cup=False):
    wb = "pokalwettbewerb" if is_cup else "wettbewerb"
    base_url = f"https://www.transfermarkt.us/{tm_slug}/elfmeterschuetzen/{wb}/{tm_code}/plus/1"
    if season_id:
        base_url += f"/saison_id/{season_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = _requests_get_with_retry(base_url, headers)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        return pd.DataFrame()
    rows = tables[1].find_all("tr")
    data = []
    current_club = None
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        row_class = row.get("class", [])
        if len(cells) == 1:
            text = cells[0].text.strip()
            skip_prefixes = ("Centre", "Right", "Left", "Attacking", "Defensive",
                             "Central", "Goalkeeper", "Second", "Sweeper")
            if text and not text.startswith(skip_prefixes):
                current_club = text
            continue
        if ("odd" in row_class or "even" in row_class) and len(cells) >= 9:
            texts = [c.text.strip() for c in cells]
            player_name = texts[2]
            total = texts[5]
            scored = texts[6]
            missed = texts[7]
            rate = texts[8]
            if player_name and current_club:
                data.append({
                    "Player": player_name,
                    "Club": current_club,
                    "Penalties": int(total) if total.isdigit() else 0,
                    "Scored": int(scored) if scored.isdigit() else 0,
                    "Missed": int(missed) if missed.isdigit() else 0,
                    "Conversion %": float(rate.replace("%", "").strip()) if "%" in rate else 0.0,
                })
    return pd.DataFrame(data)


@st.cache_data(ttl=604800, show_spinner=False)
def scrape_penalty_goalkeepers(tm_slug, tm_code, season_id=None, is_cup=False):
    wb = "pokalwettbewerb" if is_cup else "wettbewerb"
    base_url = f"https://www.transfermarkt.us/{tm_slug}/elfmetertoeter/{wb}/{tm_code}/plus/1"
    if season_id:
        base_url += f"/saison_id/{season_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = _requests_get_with_retry(base_url, headers)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        return pd.DataFrame()
    rows = tables[1].find_all("tr")
    data = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        row_class = row.get("class", [])
        if ("odd" in row_class or "even" in row_class) and len(cells) >= 9:
            texts = [c.text.strip() for c in cells]
            player_name = texts[3]
            faced = texts[-3]
            saved = texts[-2]
            ratio = texts[-1]
            club = ""
            for a in row.find_all("a"):
                href = a.get("href", "")
                if "/verein/" in href or "/club/" in href:
                    img = a.find("img")
                    if img and img.get("alt"):
                        club = img["alt"]
                        break
                    title = a.get("title", "")
                    if title:
                        club = title
                        break
            if player_name:
                data.append({
                    "Goalkeeper": player_name,
                    "Club": club,
                    "Faced": int(faced) if faced.isdigit() else 0,
                    "Saved": int(saved) if saved.isdigit() else 0,
                    "Save %": float(ratio.replace("%", "").strip()) if "%" in ratio else 0.0,
                })
    return pd.DataFrame(data)


def _tm_parse_int(s):
    clean = s.replace("'", "").replace(",", "").replace(".", "").replace("\xa0", "").strip()
    clean = clean.split("(")[0].strip()
    return int(clean) if clean.isdigit() else 0


def _parse_scorers_page(soup):
    table = soup.find("table", class_="items")
    if not table:
        tables = soup.find_all("table")
        table = tables[1] if len(tables) >= 2 else None
    if not table:
        return []

    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")
    data = []

    parse_int = _tm_parse_int

    for row in rows:
        cells = row.find_all(["td", "th"])
        row_class = row.get("class", [])
        if not ("odd" in row_class or "even" in row_class):
            continue
        if len(cells) < 10:
            continue

        player_td = row.find("td", class_="hauptlink")
        player_name = player_td.text.strip() if player_td else ""
        if not player_name:
            for c in cells:
                hl = c.find(class_="hauptlink")
                if hl:
                    player_name = hl.text.strip()
                    break

        position = cells[4].text.strip() if len(cells) > 4 else ""

        club = ""
        if len(cells) > 7:
            club_img = cells[7].find("img")
            if club_img:
                club = club_img.get("alt", "") or club_img.get("title", "")
        if not club:
            for img in row.find_all("img"):
                alt = img.get("alt", "")
                if alt and len(alt) > 2 and alt != player_name and "flag" not in alt.lower():
                    parent = img.find_parent("td")
                    parent_cls = parent.get("class", []) if parent else []
                    if "hauptlink" not in parent_cls:
                        club = alt
                        break

        appearances = parse_int(cells[8].text) if len(cells) > 8 else 0
        assists = parse_int(cells[9].text) if len(cells) > 9 else 0
        pen_goals = parse_int(cells[10].text) if len(cells) > 10 else 0

        goals_cell = row.find("td", class_=lambda c: c and "hauptlink" in c and "zentriert" in c)
        goals = 0
        if goals_cell:
            goals = parse_int(goals_cell.text)
        if goals == 0 and len(cells) > 14:
            goals = parse_int(cells[14].text)
        if goals == 0:
            goals = parse_int(cells[-1].text)

        if player_name and goals > 0:
            data.append({
                "Player": player_name,
                "Position": position,
                "Club": club,
                "Appearances": appearances,
                "Goals": goals,
                "Pen. Goals": pen_goals,
                "Open Play Goals": max(0, goals - pen_goals),
                "Assists": assists,
            })
    return data


@st.cache_data(ttl=604800, show_spinner=False)
def scrape_top_scorers(tm_slug, tm_code, season_id, is_cup=False):
    wb = "pokalwettbewerb" if is_cup else "wettbewerb"
    base_url = f"https://www.transfermarkt.us/{tm_slug}/torschuetzenliste/{wb}/{tm_code}/saison_id/{season_id}/altersklasse/alle/detailpos//plus/1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    all_data = []
    for page in range(1, 15):
        page_url = base_url if page == 1 else f"{base_url}/page/{page}"
        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()
        except Exception:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        page_data = _parse_scorers_page(soup)
        if not page_data:
            break
        all_data.extend(page_data)
        pager = soup.find("div", class_="pager")
        if not pager:
            break
        next_link = pager.find("li", class_="tm-pagination__list-item--icon-next-page")
        if not next_link or not next_link.find("a"):
            last_links = [a for a in pager.find_all("a") if f"page/{page + 1}" in a.get("href", "")]
            if not last_links:
                break

    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.sort_values("Goals", ascending=False).reset_index(drop=True)
    return df


def _parse_assists_page(soup):
    table = soup.find("table", class_="items")
    if not table:
        tables = soup.find_all("table")
        table = tables[1] if len(tables) >= 2 else None
    if not table:
        return []
    tbody = table.find("tbody") or table
    data = []
    rows = tbody.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        player_name = ""
        for c in cells:
            hl = c.find(class_="hauptlink")
            if hl:
                player_name = hl.text.strip()
                break

        position = cells[4].text.strip() if len(cells) > 4 else ""

        club = ""
        if len(cells) > 7:
            club_img = cells[7].find("img")
            if club_img:
                club = club_img.get("alt", "") or club_img.get("title", "")
        if not club:
            for img in row.find_all("img"):
                alt = img.get("alt", "")
                if alt and len(alt) > 2 and alt != player_name and "flag" not in alt.lower():
                    parent = img.find_parent("td")
                    parent_cls = parent.get("class", []) if parent else []
                    if "hauptlink" not in parent_cls:
                        club = alt
                        break

        appearances = _tm_parse_int(cells[8].text) if len(cells) > 8 else 0
        assists = _tm_parse_int(cells[9].text) if len(cells) > 9 else 0

        if player_name and assists > 0:
            data.append({
                "Player": player_name,
                "Position": position,
                "Club": club,
                "Appearances": appearances,
                "Assists": assists,
            })
    return data


@st.cache_data(ttl=604800, show_spinner=False)
def scrape_top_assists(tm_slug, tm_code, season_id, is_cup=False):
    wb = "pokalwettbewerb" if is_cup else "wettbewerb"
    base_url = f"https://www.transfermarkt.us/{tm_slug}/assistliste/{wb}/{tm_code}/saison_id/{season_id}/plus/1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    all_data = []
    for page in range(1, 15):
        page_url = base_url if page == 1 else f"{base_url}/page/{page}"
        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()
        except Exception:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        page_data = _parse_assists_page(soup)
        if not page_data:
            break
        all_data.extend(page_data)
        pager = soup.find("div", class_="pager")
        if not pager:
            break
        next_link = pager.find("li", class_="tm-pagination__list-item--icon-next-page")
        if not next_link or not next_link.find("a"):
            last_links = [a for a in pager.find_all("a") if f"page/{page + 1}" in a.get("href", "")]
            if not last_links:
                break

    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.sort_values("Assists", ascending=False).reset_index(drop=True)
    return df


@st.cache_data(ttl=604800, show_spinner=False)
def load_multi_season_penalties(start_year, end_year, tm_slug, tm_code, has_gk_data, season_type, is_cup=False):
    taker_frames = []
    gk_frames = []
    for yr in range(start_year, end_year + 1):
        try:
            t = scrape_penalty_takers(tm_slug, tm_code, yr, is_cup=is_cup)
            if not t.empty:
                t["Season"] = format_season_label(yr, season_type)
                taker_frames.append(t)
        except Exception:
            pass
        if has_gk_data:
            try:
                g = scrape_penalty_goalkeepers(tm_slug, tm_code, yr, is_cup=is_cup)
                if not g.empty:
                    g["Season"] = format_season_label(yr, season_type)
                    gk_frames.append(g)
            except Exception:
                pass

    all_takers = pd.concat(taker_frames, ignore_index=True) if taker_frames else pd.DataFrame()
    all_gks = pd.concat(gk_frames, ignore_index=True) if gk_frames else pd.DataFrame()

    if not all_takers.empty:
        agg_takers = all_takers.groupby(["Player", "Club"]).agg(
            Penalties=("Penalties", "sum"),
            Scored=("Scored", "sum"),
            Missed=("Missed", "sum"),
        ).reset_index()
        agg_takers["Conversion %"] = (agg_takers["Scored"] / agg_takers["Penalties"] * 100).round(1)
    else:
        agg_takers = pd.DataFrame()

    if not all_gks.empty:
        agg_gks = all_gks.groupby(["Goalkeeper", "Club"]).agg(
            Faced=("Faced", "sum"),
            Saved=("Saved", "sum"),
        ).reset_index()
        agg_gks["Save %"] = (agg_gks["Saved"] / agg_gks["Faced"] * 100).round(1)
    else:
        agg_gks = pd.DataFrame()

    return agg_takers, agg_gks


@st.cache_data(ttl=604800, show_spinner=False)
def load_alltime_taker_penalties(tm_slug, tm_code, start_year, season_type, is_cup=False, league_name=None):
    taker_frames = []
    for yr in range(start_year, CURRENT_SEASON_END + 1):
        try:
            t = scrape_penalty_takers(tm_slug, tm_code, yr, is_cup=is_cup)
            if not t.empty:
                t["Season"] = format_season_label(yr, season_type)
                taker_frames.append(t)
        except Exception:
            pass

    if not taker_frames:
        if league_name:
            fb_takers, _ = load_fallback_penalty_data(league_name)
            if not fb_takers.empty:
                fb_takers = fb_takers.copy()
                if "Club" in fb_takers.columns and "Clubs" not in fb_takers.columns:
                    fb_takers.rename(columns={"Club": "Clubs"}, inplace=True)
                for col in ["Seasons", "First_Season", "Last_Season"]:
                    if col not in fb_takers.columns:
                        fb_takers[col] = "—"
                return fb_takers
        return pd.DataFrame()

    all_takers = pd.concat(taker_frames, ignore_index=True)

    per_club = all_takers.groupby(["Player", "Club"]).agg(
        Penalties=("Penalties", "sum"),
        Scored=("Scored", "sum"),
        Missed=("Missed", "sum"),
    ).reset_index()
    clubs_list = per_club.groupby("Player")["Club"].apply(
        lambda x: ", ".join(sorted(c for c in x.unique() if c))
    ).reset_index()
    clubs_list.columns = ["Player", "Clubs"]

    agg = all_takers.groupby("Player").agg(
        Penalties=("Penalties", "sum"),
        Scored=("Scored", "sum"),
        Missed=("Missed", "sum"),
        Seasons=("Season", lambda x: len(x.unique())),
        First_Season=("Season", "min"),
        Last_Season=("Season", "max"),
    ).reset_index()
    agg = agg.merge(clubs_list, on="Player", how="left")
    agg["Conversion %"] = np.where(agg["Penalties"] > 0, (agg["Scored"] / agg["Penalties"] * 100).round(1), 0.0)
    agg = agg[agg["Player"].str.strip().astype(bool)]
    agg = agg[agg["Penalties"] > 0]
    agg = agg[["Player", "Clubs", "Seasons", "First_Season", "Last_Season",
               "Penalties", "Scored", "Missed", "Conversion %"]]
    return agg


@st.cache_data(ttl=604800, show_spinner=False)
def load_alltime_gk_penalties(tm_slug, tm_code, start_year, season_type, is_cup=False, league_name=None):
    gk_frames = []
    for yr in range(start_year, CURRENT_SEASON_END + 1):
        try:
            g = scrape_penalty_goalkeepers(tm_slug, tm_code, yr, is_cup=is_cup)
            if not g.empty:
                g["Season"] = format_season_label(yr, season_type)
                gk_frames.append(g)
        except Exception:
            pass

    if not gk_frames:
        if league_name:
            _, fb_gks = load_fallback_penalty_data(league_name)
            if not fb_gks.empty:
                fb_gks = fb_gks.copy()
                if "Club" in fb_gks.columns and "Clubs" not in fb_gks.columns:
                    fb_gks.rename(columns={"Club": "Clubs"}, inplace=True)
                for col in ["Seasons", "First_Season", "Last_Season", "Conceded"]:
                    if col not in fb_gks.columns:
                        fb_gks[col] = "—"
                return fb_gks
        return pd.DataFrame()

    all_gks = pd.concat(gk_frames, ignore_index=True)

    per_club = all_gks.groupby(["Goalkeeper", "Club"]).agg(
        Faced=("Faced", "sum"),
        Saved=("Saved", "sum"),
    ).reset_index()
    clubs_list = per_club.groupby("Goalkeeper")["Club"].apply(
        lambda x: ", ".join(sorted(c for c in x.unique() if c))
    ).reset_index()
    clubs_list.columns = ["Goalkeeper", "Clubs"]

    agg = all_gks.groupby("Goalkeeper").agg(
        Faced=("Faced", "sum"),
        Saved=("Saved", "sum"),
        Seasons=("Season", lambda x: len(x.unique())),
        First_Season=("Season", "min"),
        Last_Season=("Season", "max"),
    ).reset_index()
    agg = agg.merge(clubs_list, on="Goalkeeper", how="left")
    agg["Save %"] = (agg["Saved"] / agg["Faced"] * 100).round(1)
    agg["Conceded"] = agg["Faced"] - agg["Saved"]
    agg = agg[agg["Goalkeeper"].str.strip().astype(bool)]
    agg = agg[agg["Faced"] > 0]
    agg = agg[["Goalkeeper", "Clubs", "Seasons", "First_Season", "Last_Season",
               "Faced", "Saved", "Conceded", "Save %"]]
    return agg


@st.cache_data(ttl=604800, show_spinner=False)
def search_player_transfermarkt(query):
    url = f"https://www.transfermarkt.us/schnellsuche/ergebnis/schnellsuche?query={quote(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = _requests_get_with_retry(url, headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    seen_ids = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        if "/profil/spieler/" in href:
            parts = href.rstrip("/").split("/")
            try:
                player_id = int(parts[-1])
            except (ValueError, IndexError):
                continue
            if player_id in seen_ids:
                continue
            seen_ids.add(player_id)
            slug = parts[1] if len(parts) > 1 else ""
            name = a_tag.text.strip()
            if name and len(name) > 1 and not name.startswith("http"):
                results.append({"name": name, "slug": slug, "player_id": player_id})
    return results


@st.cache_data(ttl=604800, show_spinner=False)
def scrape_player_career_penalties(player_slug, player_id):
    url = f"https://www.transfermarkt.us/{player_slug}/elfmetertore/spieler/{player_id}/saison_id//wettbewerb_id//plus/1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = _requests_get_with_retry(url, headers)
    soup = BeautifulSoup(response.text, "html.parser")

    total_scored = 0
    header = soup.find("h2", string=lambda s: s and "Total penalties scored" in s if s else False)
    if not header:
        for h2 in soup.find_all("h2"):
            if h2.text and "penalties scored" in h2.text.lower():
                header = h2
                break
    if header:
        import re as _re
        m = _re.search(r"(\d+)", header.text)
        if m:
            total_scored = int(m.group(1))

    data = []
    tables = soup.find_all("table")
    for table in tables:
        header_row = table.find("tr")
        if not header_row:
            continue
        headers = [th.text.strip().lower() for th in header_row.find_all(["th", "td"])]
        col_map = {}
        for i, h in enumerate(headers):
            if "season" in h:
                col_map["season"] = i
            elif "competition" in h:
                col_map["competition"] = i
            elif "club" in h:
                col_map["club"] = i
            elif "date" in h:
                col_map["date"] = i
            elif "final" in h or "result" in h:
                col_map["result"] = i
            elif "minute" in h:
                col_map["minute"] = i
            elif "score" in h:
                col_map["score"] = i
            elif "goalkeeper" in h or "keeper" in h:
                col_map["gk"] = i

        if "season" not in col_map and "date" not in col_map:
            opp_idx = None
            for i, h in enumerate(headers):
                if "wappen" in h or h == "":
                    if opp_idx is None and i > col_map.get("club", 2):
                        opp_idx = i
            if opp_idx:
                col_map["opponent_img"] = opp_idx

        rows = table.find_all("tr")
        for row in rows:
            row_class = row.get("class", [])
            if "odd" not in row_class and "even" not in row_class:
                continue
            cells = row.find_all(["td", "th"])
            if len(cells) < 8:
                continue

            def get_text(idx):
                if idx is not None and idx < len(cells):
                    return cells[idx].text.strip()
                return ""

            def get_img_alt(idx):
                if idx is not None and idx < len(cells):
                    img = cells[idx].find("img")
                    if img and img.get("alt"):
                        return img["alt"]
                    a = cells[idx].find("a")
                    if a:
                        return a.get("title", "") or a.text.strip()
                return ""

            def get_link_text(idx):
                if idx is not None and idx < len(cells):
                    a = cells[idx].find("a")
                    if a:
                        return a.text.strip()
                    return cells[idx].text.strip()
                return ""

            season = get_text(col_map.get("season", 0))

            comp_idx = col_map.get("competition", 1)
            competition = get_link_text(comp_idx)
            if not competition and comp_idx < len(cells):
                competition = get_img_alt(comp_idx)

            club_idx = col_map.get("club", 2)
            club = get_img_alt(club_idx) or get_text(club_idx)

            date = get_text(col_map.get("date", 3))

            opp_idx = col_map.get("opponent_img")
            if opp_idx is None:
                opp_idx = col_map.get("date", 3) + 1
            opponent = get_img_alt(opp_idx)

            result_idx = col_map.get("result")
            if result_idx is None:
                result_idx = opp_idx + 1 if opp_idx else 5
            result = get_link_text(result_idx)

            minute = get_text(col_map.get("minute", 7))
            score_at_time = get_text(col_map.get("score", 8))

            gk_idx = col_map.get("gk")
            if gk_idx is None:
                gk_idx = len(cells) - 1
            gk = get_link_text(gk_idx)

            if season or date:
                data.append({
                    "Season": season,
                    "Competition": competition,
                    "Club": club,
                    "Date": date,
                    "Opponent": opponent,
                    "Result": result,
                    "Minute": minute,
                    "Score": score_at_time,
                    "Goalkeeper": gk,
                })

    return pd.DataFrame(data), total_scored


ZONE_PROBS = {
    "Bottom-Left":  {"Taker %": 25.2, "GK Save %": 18.5},
    "Bottom-Centre": {"Taker %": 8.3, "GK Save %": 55.0},
    "Bottom-Right": {"Taker %": 25.8, "GK Save %": 17.8},
    "Top-Left":     {"Taker %": 13.7, "GK Save %": 5.2},
    "Top-Centre":   {"Taker %": 5.5, "GK Save %": 12.0},
    "Top-Right":    {"Taker %": 14.0, "GK Save %": 4.8},
    "Mid-Left":     {"Taker %": 3.8, "GK Save %": 30.0},
    "Mid-Right":    {"Taker %": 3.7, "GK Save %": 28.0},
}

has_league_tables = league_cfg["wiki_pattern"] is not None and league_cfg.get("wiki_name") is not None

_single_season_error = None
_multi_season_error = None

try:
    if has_league_tables:
        st.session_state["_data_loading"] = True
        gps = league_cfg["games_per_season"]
        with st.spinner("Fetching league data..."):
            try:
                single_season_raw = fetch_season_data(int(season), league_cfg["wiki_pattern"], league_cfg["wiki_name"], league_cfg["season_type"])
                single_season = rebase_to_standard_season(single_season_raw, gps)
            except Exception as _e:
                _single_season_error = str(_e)
                single_season = pd.DataFrame()
            _multi_season_skipped = []
            try:
                multi_season_raw, _multi_season_skipped = load_multi_season(season_range[0], season_range[1], league_cfg["wiki_pattern"], league_cfg["wiki_name"], league_cfg["season_type"])
                multi_season = rebase_to_standard_season(multi_season_raw, gps)
            except Exception as _e:
                _multi_season_error = str(_e)
                multi_season = pd.DataFrame()
        st.session_state["_data_loading"] = False

        def _friendly_scrape_error(raw_err: str) -> str:
            e = raw_err.lower()
            if "404" in e:
                return "Wikipedia does not yet have a page for this season. It may not have started or been published yet."
            if "429" in e or "rate" in e:
                return "Wikipedia is temporarily rate-limiting requests. Please wait a minute and try again."
            if "502" in e or "503" in e or "504" in e:
                return "Wikipedia is temporarily unavailable (server error). Please try again in a few minutes."
            if "connection" in e or "timeout" in e or "timed out" in e or "network" in e:
                return "Could not reach Wikipedia — please check your internet connection and try again."
            if "no table" in e or "no match" in e or "no season" in e or "no data" in e or "valueerror" in e:
                return "Wikipedia has changed the layout of this season's page and the table could not be read. Cached data is shown below."
            return f"An unexpected error occurred while loading data from Wikipedia: {raw_err}"

        _using_fallback = False

        if _single_season_error and single_season.empty and not multi_season.empty:
            most_recent = multi_season["Season_End"].max() if "Season_End" in multi_season.columns else None
            if most_recent is not None:
                single_season = multi_season[multi_season["Season_End"] == most_recent].copy()
            friendly = _friendly_scrape_error(_single_season_error)
            st.error(f"**Live data unavailable.** {friendly}  \nShowing the most recent successfully-loaded season instead.")
        elif _single_season_error and single_season.empty:
            friendly = _friendly_scrape_error(_single_season_error)
            fallback_df = load_fallback_data(selected_league)
            if not fallback_df.empty:
                single_season = fallback_df.copy()
                _using_fallback = True
                st.error(
                    f"**Live data unavailable.** {friendly}  \n"
                    f"Showing **cached 2023-24 season data** for {selected_league} — results may not reflect the current season."
                )
            else:
                st.error(
                    f"**Live data unavailable.** {friendly}  \n"
                    f"No cached fallback is available for this competition. Please try again later."
                )

        if _multi_season_error and multi_season.empty:
            if not _using_fallback:
                friendly = _friendly_scrape_error(_multi_season_error)
                st.warning(f"**Historical data unavailable.** {friendly}  \nSome analysis tabs may show limited results.")
        elif _multi_season_skipped and not multi_season.empty:
            def _season_label_for_yr(yr):
                return format_season_label(yr, league_cfg["season_type"])
            skipped_labels = [_season_label_for_yr(y) for y in _multi_season_skipped]
            total_requested = season_range[1] - season_range[0] + 1
            loaded_count = total_requested - len(_multi_season_skipped)
            st.info(
                f"Showing data for **{loaded_count} of {total_requested} seasons**. "
                f"The following seasons could not be loaded and are excluded from analysis: "
                f"{', '.join(skipped_labels)}."
            )

        st.caption(f"**Last Updated:** {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
    else:
        single_season = pd.DataFrame()
        multi_season = pd.DataFrame()

    if has_league_tables and not single_season.empty and not multi_season.empty:
        gps = league_cfg["games_per_season"]
        has_pts = "Pts" in single_season.columns
        has_gf_ga = "GF" in single_season.columns and "GA" in single_season.columns
        has_gd = "GD" in single_season.columns

        hook_insights = []

        if has_pts and has_gf_ga and gps > 0:
            current_df = single_season.copy()
            current_df["_games_played"] = current_df.get("Pld", gps)
            current_df["_pts_pace"] = np.where(
                current_df["_games_played"] > 0,
                (current_df["Pts"] / current_df["_games_played"]) * gps,
                current_df["Pts"],
            )

            completed = multi_season[multi_season.get("Pld", 0) >= gps * 0.9] if "Pld" in multi_season.columns else multi_season
            if not completed.empty and "Pts" in completed.columns and "Squad" in completed.columns:
                hist_avg = completed.groupby("Squad")["Pts"].mean()

                overperformers = []
                underperformers = []
                for _, row in current_df.iterrows():
                    team = row.get("Squad", "")
                    if team in hist_avg.index:
                        hist = hist_avg[team]
                        projected = row["_pts_pace"]
                        diff = projected - hist
                        if diff > 5:
                            overperformers.append((team, projected, hist, diff))
                        elif diff < -5:
                            underperformers.append((team, projected, hist, diff))

                if overperformers:
                    overperformers.sort(key=lambda x: -x[3])
                    top = overperformers[0]
                    _top_proj = round(top[1])
                    _top_hist = round(top[2])
                    _top_gap = _top_proj - _top_hist
                    hook_insights.append(
                        f"**Biggest overperformer this season:** {top[0]} — on pace for **{_top_proj} pts** "
                        f"vs their historical average of {_top_hist} pts (+{_top_gap}). "
                        f"{'Can they sustain it?' if _top_gap > 10 else 'A solid step up.'}"
                    )

                if underperformers:
                    underperformers.sort(key=lambda x: x[3])
                    bot = underperformers[0]
                    _bot_proj = round(bot[1])
                    _bot_hist = round(bot[2])
                    _bot_gap = _bot_proj - _bot_hist
                    hook_insights.append(
                        f"**Biggest underperformer:** {bot[0]} — projected for **{_bot_proj} pts** "
                        f"vs historical average {_bot_hist} ({_bot_gap:+d}). "
                        f"{'Crisis mode.' if _bot_gap < -15 else 'A season to forget.'}"
                    )

                champ_pts = completed.groupby("Season").apply(lambda g: g["Pts"].max())
                if len(champ_pts) >= 3:
                    avg_title = champ_pts.mean()
                    leader = current_df.iloc[0]
                    leader_pace = leader["_pts_pace"]
                    title_gap = leader_pace - avg_title
                    leader_name = leader.get("Squad", "Leader")
                    _lp = round(leader_pace)
                    _at = round(avg_title)
                    _tgap = _lp - _at
                    if title_gap > 5:
                        hook_insights.append(
                            f"**Title odds swing:** {leader_name} is on pace for **{_lp} pts** — "
                            f"that's {_tgap} points above the historical title-winning average ({_at}). "
                            f"Dominant season in the making."
                        )
                    elif title_gap < -5:
                        hook_insights.append(
                            f"**Title race wide open:** {leader_name} leads but is on pace for just "
                            f"**{_lp} pts** — {abs(_tgap)} below the typical title-winning average of {_at}. "
                            f"Anyone's season."
                        )
                    else:
                        hook_insights.append(
                            f"**Title race:** {leader_name} tracks the historical title pace "
                            f"({_lp} pts projected vs {_at} avg). Tight at the top."
                        )

            if len(current_df) >= 2 and has_pts:
                pts_1st = current_df.iloc[0].get("Pts", 0)
                pts_2nd = current_df.iloc[1].get("Pts", 0)
                gap = pts_1st - pts_2nd
                squad_1 = current_df.iloc[0].get("Squad", "Leader")
                squad_2 = current_df.iloc[1].get("Squad", "2nd")
                games_played = current_df.iloc[0].get("_games_played", gps)
                if games_played > 0 and games_played < gps:
                    remaining = gps - games_played
                    if gap == 0:
                        hook_insights.append(
                            f"**Neck and neck:** {squad_1} and {squad_2} are level on **{pts_1st:.0f} pts** "
                            f"with {remaining:.0f} games remaining. Every match is a final."
                        )
                    elif gap <= 3:
                        hook_insights.append(
                            f"**Tight at the top:** Only **{gap:.0f} pts** separate {squad_1} ({pts_1st:.0f}) "
                            f"from {squad_2} ({pts_2nd:.0f}) with {remaining:.0f} games to go."
                        )

            if has_gf_ga:
                best_attack = current_df.loc[current_df["GF"].idxmax()]
                best_defence = current_df.loc[current_df["GA"].idxmin()]
                worst_defence = current_df.loc[current_df["GA"].idxmax()]
                best_att_name = best_attack.get("Squad", "")
                best_def_name = best_defence.get("Squad", "")
                worst_def_name = worst_defence.get("Squad", "")
                best_att_gf = best_attack["GF"]
                best_att_pld = best_attack.get("_games_played", gps)
                best_def_ga = best_defence["GA"]
                best_def_pld = best_defence.get("_games_played", gps)
                worst_def_ga = worst_defence["GA"]
                worst_def_pld = worst_defence.get("_games_played", gps)

                if best_att_pld > 0:
                    att_rate = best_att_gf / best_att_pld
                    hook_insights.append(
                        f"**Best attack:** {best_att_name} leads the scoring charts with **{best_att_gf:.0f} goals** "
                        f"({att_rate:.2f} per game)."
                    )
                if best_def_pld > 0:
                    def_rate = best_def_ga / best_def_pld
                    hook_insights.append(
                        f"**Tightest defence:** {best_def_name} — just **{best_def_ga:.0f} goals conceded** "
                        f"({def_rate:.2f} per game)."
                    )
                if worst_def_name != best_def_name and worst_def_pld > 0:
                    leak_rate = worst_def_ga / worst_def_pld
                    if leak_rate > 2.0:
                        hook_insights.append(
                            f"**Leakiest defence:** {worst_def_name} have conceded **{worst_def_ga:.0f} goals** "
                            f"({leak_rate:.2f} per game) — a defensive rebuild is needed."
                        )

            if has_gd and len(current_df) >= 5:
                bottom_5 = current_df.tail(5)
                relegation_battle = bottom_5[bottom_5["GD"] < 0]
                if len(relegation_battle) >= 3:
                    worst = relegation_battle.iloc[-1]
                    worst_name = worst.get("Squad", "")
                    worst_gd = worst["GD"]
                    hook_insights.append(
                        f"**Relegation watch:** {worst_name} sit bottom with a goal difference of "
                        f"**{worst_gd:+.0f}** — time is running out."
                    )

        if hook_insights:
            st.markdown(
                f'<div class="anim-insight-header">'
                f'<span style="font-size:1.15em;font-weight:bold;color:#00d4ff;">&#9889; This Week\'s Insights — {selected_league}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for insight in hook_insights:
                st.markdown(f"- {insight}")
            st.markdown("")

    if has_league_tables:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "League Table",
            "Statistical Analysis",
            "Visualizations",
            "Predictions & Insights",
            "Penalty Analysis",
            "Team Insights",
            "League Comparisons",
        ])
        if not multi_season.empty and "Squad" in multi_season.columns:
            _all_teams_sidebar = sorted(multi_season["Squad"].unique().tolist())
            with st.sidebar:
                st.divider()
                st.subheader("Team Insights")
                selected_team = st.selectbox("Select a team", _all_teams_sidebar, key="team_insights_select")
        else:
            selected_team = None
    else:
        tab5, = st.tabs(["Penalty Analysis"])
        selected_team = None

    if has_league_tables:
        season_label = format_season_label(season, league_cfg["season_type"])

        n_rebased = int(multi_season["Rebased"].sum()) if "Rebased" in multi_season.columns else 0
        rebased_seasons = sorted(multi_season.loc[multi_season.get("Rebased", False) == True, "Season"].unique().tolist()) if n_rebased > 0 else []
        rebased_detail = {}
        if n_rebased > 0 and "Original_Pld" in multi_season.columns:
            rb_rows = multi_season[multi_season.get("Rebased", False) == True]
            for s in rebased_seasons:
                orig = int(rb_rows.loc[rb_rows["Season"] == s, "Original_Pld"].mode().iloc[0])
                rebased_detail.setdefault(orig, []).append(s)
        single_rebased = bool(single_season.get("Rebased", pd.Series([False])).any()) if "Rebased" in single_season.columns else False

        with tab1:
            st.subheader(f"{selected_league} {season_label} Standings")
            if single_rebased and "Original_Pld" in single_season.columns:
                orig_pld = int(single_season["Original_Pld"].iloc[0])
                st.info(
                    f"This season originally had **{orig_pld} games** per team (different league size). "
                    f"All stats have been rebased to a **{league_cfg['games_per_season']}-game** standard for fair comparison across seasons."
                )
            display_cols = [c for c in ["Pos", "Squad", "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts", "PPG", "Win%"] if c in single_season.columns]
            n_teams = league_cfg["teams"]
            table_height = max(200, min(740, 40 + n_teams * 35))
            st.dataframe(
                single_season[display_cols].set_index("Pos"),
                use_container_width=True,
                height=table_height,
            )
            share_table_buttons(single_season[display_cols], f"{selected_league} {season_label} Table", f"league_table_{season}")

            if "Pld" in single_season.columns and gps > 0:
                _gp_now = int(single_season["Pld"].max())
                _prog = min(100.0, _gp_now / gps * 100)
                _is_live = _prog < 99.5
                _status_html = '<span class="live-badge">LIVE</span>' if _is_live else '<span class="complete-badge">&#10003; COMPLETE</span>'
                st.markdown(
                    f'<div style="margin-bottom:2px;">'
                    f'<span style="font-size:0.88em;color:#aaa;">Season progress: {_gp_now} / {gps} matchdays</span>'
                    f'{_status_html}</div>'
                    f'<div class="season-progress-wrap">'
                    f'<div class="season-progress-bar" style="width:{_prog:.1f}%"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            if "GF" in single_season.columns and "GA" in single_season.columns:
                st.subheader("Goals Scored vs Conceded")
                fig_goals = go.Figure()
                fig_goals.add_trace(go.Bar(
                    name="Goals For",
                    x=single_season["Squad"],
                    y=single_season["GF"],
                    marker_color="#2ecc71",
                ))
                fig_goals.add_trace(go.Bar(
                    name="Goals Against",
                    x=single_season["Squad"],
                    y=single_season["GA"],
                    marker_color="#e74c3c",
                ))
                fig_goals.update_layout(barmode="group", xaxis_tickangle=-45, height=450)
                st.plotly_chart(fig_goals, use_container_width=True)

        with tab2:
            st.subheader("What Statistically Drives League Points?")
            range_start_label = format_season_label(season_range[0], league_cfg["season_type"])
            range_end_label = format_season_label(season_range[1], league_cfg["season_type"])
            st.markdown(
                f"Analysis based on **{len(multi_season)}** team-season observations "
                f"across **{multi_season['Season_End'].nunique()}** seasons "
                f"({range_start_label} to {range_end_label})."
            )
            if rebased_seasons:
                n_rb_seasons = len(set(rebased_seasons))
                detail_parts = []
                for orig_pld, seasons in sorted(rebased_detail.items()):
                    detail_parts.append(f"{len(seasons)} season(s) originally had {orig_pld} games: {', '.join(seasons)}")
                detail_str = "; ".join(detail_parts) if detail_parts else f"{n_rb_seasons} season(s)"
                st.caption(
                    f"Note: {detail_str} — all rebased to the current {league_cfg['games_per_season']}-game standard for fair comparison."
                )

            numeric_vars = ["W", "D", "L", "GF", "GA", "GD", "Pts", "PPG", "Win%", "GF/Game", "GA/Game"]
            available_vars = [v for v in numeric_vars if v in multi_season.columns]
            corr_data = multi_season[available_vars].dropna()

            st.subheader("Descriptive Statistics")
            st.markdown("Summary of key variables across all selected seasons.")

            desc_vars = [v for v in ["W", "D", "L", "GF", "GA", "GD", "Pts", "PPG", "Win%", "GF/Game", "GA/Game"] if v in multi_season.columns]
            desc_data = multi_season[desc_vars].dropna()
            desc_table = desc_data.describe().T
            desc_table["Variance"] = desc_data.var()
            desc_table = desc_table[["count", "mean", "std", "Variance", "min", "25%", "50%", "75%", "max"]]
            desc_table.columns = ["Count", "Mean", "Std. Dev.", "Variance", "Min", "25th %ile", "Median", "75th %ile", "Max"]
            st.dataframe(desc_table.round(3), use_container_width=True)

            with st.expander("Formulas: Descriptive Statistics", expanded=False):
                st.latex(r"\text{Mean} \;(\bar{x}) = \frac{1}{n}\sum_{i=1}^{n} x_i")
                st.markdown("The average value — add up all values and divide by how many there are.")
                st.latex(r"\text{Variance} \;(\sigma^2) = \frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2")
                st.markdown("How spread out the values are from the average. Larger = more spread.")
                st.latex(r"\text{Standard Deviation} \;(\sigma) = \sqrt{\text{Variance}}")
                st.markdown("Same idea as variance but in the original units (e.g. points, goals), which makes it easier to interpret.")

            st.divider()

            st.subheader("Correlation Matrix")
            st.markdown(
                "The correlation matrix shows how strongly each pair of stats moves together. "
                "Values range from **-1** (when one goes up, the other goes down) to **+1** "
                "(both move in the same direction). Values near **0** mean little relationship."
            )
            corr_matrix = corr_data.corr()
            fig_corr = px.imshow(
                corr_matrix,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1,
                aspect="equal",
            )
            fig_corr.update_layout(
                height=600,
                xaxis=dict(tickangle=-45, tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                margin=dict(l=100, r=20, t=20, b=100),
            )
            fig_corr.update_traces(
                textfont=dict(size=11),
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            if "GD" in corr_matrix.columns and "Pts" in corr_matrix.columns:
                gd_pts = corr_matrix.loc["GD", "Pts"]
                gf_pts = corr_matrix.loc["GF", "Pts"] if "GF" in corr_matrix.columns else None
                ga_pts = corr_matrix.loc["GA", "Pts"] if "GA" in corr_matrix.columns else None
                _corr_lines = []
                if gd_pts is not None:
                    _corr_lines.append(
                        f"- **Goal Difference vs Points** (r = {gd_pts:.2f}): "
                        + ("Extremely strong — the more goals a team scores *relative to those conceded*, the more points they almost always get." if gd_pts >= 0.9
                           else "Strong — goal difference is a reliable indicator of points." if gd_pts >= 0.75
                           else "Moderate — goal difference is related to points but other factors also matter.")
                    )
                if gf_pts is not None:
                    _corr_lines.append(
                        f"- **Goals Scored vs Points** (r = {gf_pts:.2f}): "
                        + ("Very strong — scoring lots of goals is closely tied to winning points." if gf_pts >= 0.8
                           else "Moderate — scoring goals helps, but it doesn't guarantee points on its own." if gf_pts >= 0.5
                           else "Weak — in this league, points come from more than just scoring goals.")
                    )
                if ga_pts is not None:
                    _corr_lines.append(
                        f"- **Goals Conceded vs Points** (r = {ga_pts:.2f}): "
                        + ("Very strong negative — teams that concede a lot consistently end up with few points." if ga_pts <= -0.8
                           else "Moderate negative — conceding fewer goals tends to mean more points." if ga_pts <= -0.5
                           else "Weak negative — in this league, conceding doesn't damage points as much as you might expect.")
                    )
                st.info(
                    "**What does this chart tell us — in plain English?**\n\n"
                    + "\n".join(_corr_lines)
                    + "\n\n*Hover over any cell for the exact value. "
                    "Darker blue = strong positive link; darker red = strong negative link; white = no relationship.*"
                )

            with st.expander("Formula: Pearson Correlation Coefficient", expanded=False):
                st.latex(r"r_{xy} = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2 \;\cdot\; \sum_{i=1}^{n}(y_i - \bar{y})^2}}")
                st.markdown(
                    "This measures the linear relationship between two variables. "
                    "**r = +1** means a perfect positive relationship (both go up together), "
                    "**r = -1** means a perfect negative relationship (one goes up, the other goes down), "
                    "and **r = 0** means no linear relationship."
                )

            st.markdown("**Key abbreviations:** W = Wins, D = Draws, L = Losses, "
                         "GF = Goals For (scored), GA = Goals Against (conceded), "
                         "GD = Goal Difference (GF minus GA), Pts = Points, "
                         "PPG = Points Per Game, Win% = Win Percentage, "
                         "GF/Game = Goals scored per match, GA/Game = Goals conceded per match.")

            st.divider()
            st.subheader("OLS Regression: What Predicts League Points?")
            st.info(
                "**What is OLS? (Ordinary Least Squares)**\n\n"
                "Imagine drawing the single best straight line through a cloud of dots on a graph — "
                "that's essentially what OLS does. It looks at *every* season in the data (from the very first to the most recent) "
                "and treats them all as equally important. It finds the formula that is, on average, closest to all the data points.\n\n"
                "**In plain English:** OLS answers the question — *across all seasons ever played, how many extra points does a team "
                "earn for each additional goal scored, and how many points do they lose for each goal conceded?*"
            )

            with st.expander("Formula: OLS Regression", expanded=False):
                st.latex(r"\hat{y} = b_0 + b_1 x_1 + b_2 x_2 + \cdots + b_k x_k")
                st.markdown(
                    "Where:\n"
                    "- **y-hat** is the predicted value (e.g. Points)\n"
                    "- **b₀** is the baseline (intercept) — the predicted value when all inputs are zero\n"
                    "- **b₁, b₂, ...** are the coefficients — how much each input contributes\n"
                    "- **x₁, x₂, ...** are the input variables (e.g. Goals Scored, Goals Conceded)\n\n"
                    "OLS finds the values of b₀, b₁, b₂... that minimise the sum of squared errors:"
                )
                st.latex(r"\min \sum_{i=1}^{n}(y_i - \hat{y}_i)^2")
                st.markdown("In other words, it finds the line (or surface) that is closest to all the data points.")

            st.markdown(
                "**Model 1:** We predict a team's **Points** using their **Goals Scored (GF)** "
                "and **Goals Conceded (GA)**."
            )

            if "GF" in multi_season.columns and "GA" in multi_season.columns:
                reg_data = multi_season[["Pts", "GF", "GA"]].dropna()
                X = sm.add_constant(reg_data[["GF", "GA"]])
                y = reg_data["Pts"]
                model = sm.OLS(y, X).fit()

                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("R-squared", f"{model.rsquared:.4f}")
                col_r2.metric("Adj. R-squared", f"{model.rsquared_adj:.4f}")
                col_r3.metric("F-statistic", f"{model.fvalue:.2f}")

                with st.expander("Formulas: Model Diagnostics", expanded=False):
                    st.latex(r"R^2 = 1 - \frac{\sum(y_i - \hat{y}_i)^2}{\sum(y_i - \bar{y})^2}")
                    st.markdown("**R-squared**: The proportion of variation in Points explained by the model. 1.0 = perfect fit, 0.0 = explains nothing.")
                    st.latex(r"\bar{R}^2 = 1 - (1 - R^2)\frac{n-1}{n-k-1}")
                    st.markdown("**Adjusted R-squared**: Penalises R-squared for adding more variables. Prevents overfitting — only rises if a new variable genuinely helps.")
                    st.latex(r"F = \frac{R^2 / k}{(1-R^2)/(n-k-1)}")
                    st.markdown("**F-statistic**: Tests whether the model as a whole is meaningful. Higher = stronger evidence that at least one variable matters. n = number of observations, k = number of variables.")

                st.markdown("**How much does each factor contribute?**")
                coef_df = pd.DataFrame({
                    "Factor": ["Baseline (starting points)", "Goals Scored (GF)", "Goals Conceded (GA)"],
                    "Effect on Points": model.params.values.round(4),
                    "Std. Error": model.bse.values.round(4),
                    "Confidence (t-value)": model.tvalues.values.round(4),
                    "Significance (p-value)": model.pvalues.values.round(6),
                })
                st.dataframe(coef_df.set_index("Factor"), use_container_width=True)

                with st.expander("Formulas: Coefficient Statistics", expanded=False):
                    st.latex(r"\text{Std. Error}(b_j) = \sqrt{\frac{\hat{\sigma}^2}{(1-R_j^2)\sum(x_{ij}-\bar{x}_j)^2}}")
                    st.markdown("**Standard Error**: How precise the coefficient estimate is. Smaller = more precise.")
                    st.latex(r"t = \frac{b_j}{\text{Std. Error}(b_j)}")
                    st.markdown("**t-value**: The coefficient divided by its standard error. Values above 2 (or below -2) are generally reliable.")
                    st.markdown("**p-value**: The probability of seeing this result if the variable had no real effect. Below 0.05 = statistically significant (very unlikely to be random chance).")

                st.markdown(
                    f"**In plain English:** Each additional goal scored is associated with "
                    f"**{model.params['GF']:.3f}** more points, while each additional goal "
                    f"conceded is associated with **{model.params['GA']:.3f}** points "
                    f"(holding the other constant). The model explains **{model.rsquared * 100:.1f}%** "
                    f"of the variation in league points."
                )

            st.divider()
            st.subheader("Model 1b: Recent Era (Last 5 Completed Seasons)")
            st.markdown(
                f"The {selected_league} has changed significantly over time. "
                "This model uses only the **last 5 completed seasons** to "
                "capture current dynamics more accurately."
            )

            recent_cutoff = CURRENT_SEASON_END - 5
            recent_era = multi_season[
                (multi_season["Season_End"] >= recent_cutoff) &
                (multi_season["Season_End"] < CURRENT_SEASON_END)
            ]
            if not recent_era.empty and "GF" in recent_era.columns and "GA" in recent_era.columns:
                reg_recent = recent_era[["Pts", "GF", "GA"]].dropna()
                if len(reg_recent) > 5:
                    X_rec = sm.add_constant(reg_recent[["GF", "GA"]])
                    y_rec = reg_recent["Pts"]
                    model_rec = sm.OLS(y_rec, X_rec).fit()

                    recent_start_label = format_season_label(recent_cutoff, league_cfg["season_type"])
                    recent_end_label = format_season_label(CURRENT_SEASON_END - 1, league_cfg["season_type"])
                    st.markdown(f"*Using {len(reg_recent)} team-seasons from {recent_start_label} to {recent_end_label}*")

                    rcol1, rcol2, rcol3 = st.columns(3)
                    rcol1.metric("R-squared", f"{model_rec.rsquared:.4f}")
                    rcol2.metric("Adj. R-squared", f"{model_rec.rsquared_adj:.4f}")
                    rcol3.metric("F-statistic", f"{model_rec.fvalue:.2f}")

                    coef_rec = pd.DataFrame({
                        "Factor": ["Baseline (starting points)", "Goals Scored (GF)", "Goals Conceded (GA)"],
                        "Effect on Points": model_rec.params.values.round(4),
                        "Std. Error": model_rec.bse.values.round(4),
                        "Confidence (t-value)": model_rec.tvalues.values.round(4),
                        "Significance (p-value)": model_rec.pvalues.values.round(6),
                    })
                    st.dataframe(coef_rec.set_index("Factor"), use_container_width=True)

                    st.markdown("**Comparison: Full History vs Recent Era**")
                    if "GF" in multi_season.columns:
                        comp_data = pd.DataFrame({
                            "Metric": ["R-squared", "GF coefficient", "GA coefficient", "Observations"],
                            f"Full History ({multi_season['Season_End'].min():.0f}-{multi_season['Season_End'].max():.0f})": [
                                f"{model.rsquared:.4f}",
                                f"{model.params['GF']:.4f}",
                                f"{model.params['GA']:.4f}",
                                f"{len(reg_data)}",
                            ],
                            f"Recent 5 Seasons ({recent_cutoff}-{CURRENT_SEASON_END - 1})": [
                                f"{model_rec.rsquared:.4f}",
                                f"{model_rec.params['GF']:.4f}",
                                f"{model_rec.params['GA']:.4f}",
                                f"{len(reg_recent)}",
                            ],
                        })
                        st.dataframe(comp_data.set_index("Metric"), use_container_width=True)

                    gf_diff = model_rec.params["GF"] - model.params["GF"]
                    ga_diff = model_rec.params["GA"] - model.params["GA"]
                    st.markdown(
                        f"**In plain English:** In the recent era, each goal scored is worth "
                        f"{'more' if gf_diff > 0 else 'less'} ({model_rec.params['GF']:.3f} vs {model.params['GF']:.3f}) "
                        f"and each goal conceded costs "
                        f"{'more' if abs(model_rec.params['GA']) > abs(model.params['GA']) else 'less'} "
                        f"({model_rec.params['GA']:.3f} vs {model.params['GA']:.3f}). "
                        f"{'The widening gap between top and bottom teams means goals have a stronger impact on points in recent seasons.' if abs(gf_diff) > 0.01 or abs(ga_diff) > 0.01 else 'The relationship has remained relatively stable.'}"
                    )
            else:
                st.info("Not enough recent completed seasons in the selected range to build this model.")

            st.divider()
            st.subheader("Model 2: Points from Match Results")
            st.markdown(
                "**Model 2:** We predict **Points** using **Wins (W)**, **Draws (D)**, and **Losses (L)** "
                "— the direct match outcomes."
            )

            if "W" in multi_season.columns and "D" in multi_season.columns and "L" in multi_season.columns:
                reg_data2 = multi_season[["Pts", "W", "D", "L"]].dropna()
                X2 = sm.add_constant(reg_data2[["W", "D", "L"]])
                y2 = reg_data2["Pts"]
                model2 = sm.OLS(y2, X2).fit()

                col_e1, col_e2, col_e3 = st.columns(3)
                col_e1.metric("R-squared", f"{model2.rsquared:.4f}")
                col_e2.metric("Adj. R-squared", f"{model2.rsquared_adj:.4f}")
                col_e3.metric("F-statistic", f"{model2.fvalue:.2f}")

                coef_df2 = pd.DataFrame({
                    "Factor": ["Baseline", "Wins (W)", "Draws (D)", "Losses (L)"],
                    "Effect on Points": model2.params.values.round(4),
                    "Std. Error": model2.bse.values.round(4),
                    "Confidence (t-value)": model2.tvalues.values.round(4),
                    "Significance (p-value)": model2.pvalues.values.round(6),
                })
                st.dataframe(coef_df2.set_index("Factor"), use_container_width=True)

                st.markdown(
                    f"**In plain English:** As expected, each win contributes ~3 points "
                    f"(coefficient = {model2.params['W']:.2f}) and each draw ~1 point "
                    f"(coefficient = {model2.params['D']:.2f}). The near-perfect R-squared "
                    f"({model2.rsquared:.4f}) confirms this — points are directly determined by results."
                )

        with tab3:
            st.subheader("Exploratory Visualizations")
            st.info(
                "**How to read these charts:**\n\n"
                "Each dot represents one team in one season. The **diagonal line** (trendline) shows the overall pattern — "
                "whether teams that score more goals (or concede fewer) tend to finish with more points.\n\n"
                "- **Steeper upward line** = stronger relationship between that stat and points\n"
                "- **Dots spread far from the line** = the relationship is noisy (other things also matter)\n"
                "- **Dots clustered close to the line** = the stat is a reliable predictor of points\n\n"
                "You can hover over any dot to see which team and season it represents."
            )

            col_v1, col_v2 = st.columns(2)

            with col_v1:
                st.markdown("**Goals Scored vs Points**")
                if "GF" in multi_season.columns:
                    fig_scatter1 = px.scatter(
                        multi_season, x="GF", y="Pts",
                        color="Season", hover_data=["Squad"],
                        trendline="ols",
                        labels={"GF": "Goals Scored", "Pts": "Points"},
                    )
                    fig_scatter1.update_layout(height=400)
                    st.plotly_chart(fig_scatter1, use_container_width=True)

            with col_v2:
                st.markdown("**Goals Conceded vs Points**")
                if "GA" in multi_season.columns:
                    fig_scatter2 = px.scatter(
                        multi_season, x="GA", y="Pts",
                        color="Season", hover_data=["Squad"],
                        trendline="ols",
                        labels={"GA": "Goals Conceded", "Pts": "Points"},
                    )
                    fig_scatter2.update_layout(height=400)
                    st.plotly_chart(fig_scatter2, use_container_width=True)

            st.divider()

            st.markdown("**Goal Difference vs Points**")
            if "GD" in multi_season.columns:
                fig_gd = px.scatter(
                    multi_season, x="GD", y="Pts",
                    color="Season", hover_data=["Squad"],
                    trendline="ols",
                    labels={"GD": "Goal Difference", "Pts": "Points"},
                )
                fig_gd.update_layout(height=450)
                st.plotly_chart(fig_gd, use_container_width=True)

                r_val, p_val = stats.pearsonr(multi_season["GD"].dropna(), multi_season.loc[multi_season["GD"].notna(), "Pts"])
                st.markdown(
                    f"**Pearson correlation** between Goal Difference and Points: "
                    f"**r = {r_val:.4f}** (p = {p_val:.2e}). "
                    f"Goal difference is one of the strongest single predictors of league points."
                )

            st.divider()

            st.markdown("**Points Distribution by Position Tier**")
            tier_data = multi_season.copy()
            n = league_cfg["teams"]
            if n >= 18:
                bins = [0, 4, 7, n // 2 + 1, n]
                labels = ["Top 4", "5th-7th", f"8th-{n // 2}th", f"{n // 2 + 1}th-{n}th"]
            elif n >= 12:
                bins = [0, 3, 6, n // 2 + 1, n]
                labels = ["Top 3", "4th-6th", f"7th-{n // 2}th", f"{n // 2 + 1}th-{n}th"]
            else:
                bins = [0, 2, 4, n // 2 + 1, n]
                labels = ["Top 2", "3rd-4th", f"5th-{n // 2}th", f"{n // 2 + 1}th-{n}th"]
            tier_data["Tier"] = pd.cut(
                tier_data["Pos"],
                bins=bins,
                labels=labels,
            )
            fig_box = px.box(
                tier_data, x="Tier", y="Pts",
                color="Tier",
                labels={"Tier": "Position Tier", "Pts": "Points"},
            )
            fig_box.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

            st.divider()

            st.markdown("**Champion Points Over Seasons**")
            champions = multi_season[multi_season["Pos"] == 1].sort_values("Season_End")
            if not champions.empty:
                fig_champ = go.Figure()
                fig_champ.add_trace(go.Scatter(
                    x=champions["Season"],
                    y=champions["Pts"],
                    mode="lines+markers+text",
                    text=champions["Squad"],
                    textposition="top center",
                    marker=dict(size=10, color="#f1c40f"),
                    line=dict(color="#f1c40f", width=2),
                ))
                fig_champ.update_layout(
                    yaxis_title="Points",
                    height=400,
                )
                st.plotly_chart(fig_champ, use_container_width=True)

        with tab4:
            st.subheader("Predictions & Insights")

            st.markdown("### Points Predictor")
            st.markdown(
                "Estimate expected points using **two models**: one trained on the full history, "
                "and one on just the last 5 completed seasons (which better reflects the modern game)."
            )

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pred_gf = st.number_input("Goals Scored", min_value=10, max_value=120, value=60, step=1)
            with col_p2:
                pred_ga = st.number_input("Goals Conceded", min_value=10, max_value=120, value=45, step=1)

            if "GF" in multi_season.columns and "GA" in multi_season.columns:
                reg_data_pred = multi_season[["Pts", "GF", "GA"]].dropna()
                X_pred = sm.add_constant(reg_data_pred[["GF", "GA"]])
                y_pred = reg_data_pred["Pts"]
                model_pred = sm.OLS(y_pred, X_pred).fit()

                new_X = pd.DataFrame({"const": [1], "GF": [pred_gf], "GA": [pred_ga]})
                predicted_pts = model_pred.predict(new_X)[0]
                prediction_interval = model_pred.get_prediction(new_X)
                pi = prediction_interval.conf_int(alpha=0.05)[0]

                pred_cutoff = CURRENT_SEASON_END - 5
                recent_pred_data = multi_season[
                    (multi_season["Season_End"] >= pred_cutoff) &
                    (multi_season["Season_End"] < CURRENT_SEASON_END)
                ][["Pts", "GF", "GA"]].dropna()

                has_recent_model = len(recent_pred_data) > 5
                if has_recent_model:
                    X_rpred = sm.add_constant(recent_pred_data[["GF", "GA"]])
                    y_rpred = recent_pred_data["Pts"]
                    model_rpred = sm.OLS(y_rpred, X_rpred).fit()
                    predicted_pts_recent = model_rpred.predict(new_X)[0]
                    pi_recent = model_rpred.get_prediction(new_X).conf_int(alpha=0.05)[0]

                st.markdown("**Full History Model**")
                col_pred1, col_pred2, col_pred3 = st.columns(3)
                col_pred1.metric("Predicted Points", f"{predicted_pts:.1f}")
                col_pred2.metric("95% CI Lower", f"{pi[0]:.1f}")
                col_pred3.metric("95% CI Upper", f"{pi[1]:.1f}")

                if has_recent_model:
                    st.markdown(f"**Recent Era Model (last 5 seasons)**")
                    col_rp1, col_rp2, col_rp3 = st.columns(3)
                    col_rp1.metric("Predicted Points", f"{predicted_pts_recent:.1f}",
                                   delta=f"{predicted_pts_recent - predicted_pts:+.1f} vs full history")
                    col_rp2.metric("95% CI Lower", f"{pi_recent[0]:.1f}")
                    col_rp3.metric("95% CI Upper", f"{pi_recent[1]:.1f}")

                best_pred = predicted_pts_recent if has_recent_model else predicted_pts
                completed_seasons = multi_season[multi_season["Season_End"] < CURRENT_SEASON_END]
                if completed_seasons.empty:
                    completed_seasons = multi_season
                recent = completed_seasons[completed_seasons["Season_End"] == completed_seasons["Season_End"].max()]
                if not recent.empty:
                    closest = recent.iloc[(recent["Pts"] - best_pred).abs().argsort()[:1]]
                    recent_label = format_season_label(int(closest["Season_End"].values[0]), league_cfg["season_type"])
                    model_label = "recent era model" if has_recent_model else "full history model"
                    st.markdown(
                        f"A team with {pred_gf} goals scored and {pred_ga} conceded would be expected to "
                        f"finish with approximately **{best_pred:.0f} points** (using the {model_label}), "
                        f"similar to **{closest['Squad'].values[0]}** ({closest['Pts'].values[0]:.0f} pts) "
                        f"in the {recent_label} season."
                    )

                _best_pi = pi_recent if has_recent_model else pi
                st.info(
                    f"**What do these numbers mean?**\n\n"
                    f"The model predicts **{best_pred:.0f} points** for a team that scores {pred_gf} goals "
                    f"and concedes {pred_ga}. Think of this as the most likely outcome based on historical patterns "
                    f"in the {selected_league}.\n\n"
                    f"The **95% Confidence Interval ({_best_pi[0]:.0f} – {_best_pi[1]:.0f} pts)** is the range "
                    f"within which the actual points total would fall 19 times out of 20, given this goal record. "
                    f"A wider range means the league has more unpredictability; a narrower range means "
                    f"goals are a very reliable predictor of points in this competition.\n\n"
                    f"*Note: this prediction assumes a full season of {gps} games played.*"
                )

                st.divider()
                st.markdown("**Form-Weighted Model (Exponential Decay / WLS)**")
                st.info(
                    "**What is WLS? (Weighted Least Squares)**\n\n"
                    "WLS works the same way as OLS — it still finds the best-fit formula — but instead of treating every season "
                    "equally, it gives *more importance to recent seasons* and less to older ones. "
                    "Think of it like asking a scout: *what matters in today's football?* not *what mattered on average across the last 30 years?*\n\n"
                    "Here, each season back in time is worth 15% less than the one before it (λ = 0.85). So last season counts almost fully, "
                    "five seasons ago counts about half as much, and seasons from 10+ years ago barely influence the result.\n\n"
                    "**Why does this matter?** Modern football has changed — more goals are scored, tactics have evolved, and transfer fees "
                    "have inflated. The WLS model captures *current* patterns rather than blending them with old ones.\n\n"
                    "**OLS vs WLS at a glance:**\n"
                    "- **OLS** = treats 1995 and 2024 the same — best for understanding long-run averages\n"
                    "- **WLS** = weights 2024 much more than 1995 — best for predicting *today's* performance"
                )
                st.markdown(
                    "This model assigns **exponentially higher weight to recent seasons** (λ = 0.85 per season back) "
                    "so current tactical trends, transfer inflation, and competitive dynamics have more influence "
                    "than data from 10+ years ago. A **Weighted Least Squares (WLS)** regression is fitted using these weights."
                )
                if "Season_End" in multi_season.columns:
                    _fw = multi_season[["Pts", "GF", "GA", "Season_End"]].dropna().copy()
                    if len(_fw) > 5:
                        _max_se = int(_fw["Season_End"].max())
                        _fw["_wt"] = 0.85 ** (_max_se - _fw["Season_End"])
                        _X_wls = sm.add_constant(_fw[["GF", "GA"]])
                        _model_wls = sm.WLS(_fw["Pts"], _X_wls, weights=_fw["_wt"]).fit()
                        _pred_wls = _model_wls.predict(new_X)[0]
                        _wc1, _wc2, _wc3 = st.columns(3)
                        _wc1.metric(
                            "Form-Weighted Prediction",
                            f"{_pred_wls:.1f} pts",
                            f"{_pred_wls - predicted_pts:+.1f} vs OLS full history",
                        )
                        _wc2.metric("R² (weighted)", f"{_model_wls.rsquared:.4f}")
                        _wc3.metric(
                            "GF / |GA| coefficient",
                            f"{_model_wls.params['GF']:.3f} / {abs(_model_wls.params['GA']):.3f}",
                        )
                        _gf_chg = _model_wls.params["GF"] - model_pred.params["GF"]
                        _ga_chg = abs(_model_wls.params["GA"]) - abs(model_pred.params["GA"])
                        st.markdown(
                            f"In the form-weighted model, each goal scored is worth **{_model_wls.params['GF']:.3f} pts** "
                            f"({'↑ more' if _gf_chg > 0.001 else '↓ less' if _gf_chg < -0.001 else '≈ same'} than full-history OLS value of {model_pred.params['GF']:.3f}), "
                            f"and each goal conceded costs **{abs(_model_wls.params['GA']):.3f} pts** "
                            f"({'↑ more costly' if _ga_chg > 0.001 else '↓ less costly' if _ga_chg < -0.001 else '≈ unchanged'} vs {abs(model_pred.params['GA']):.3f}). "
                            f"{'Recent seasons show goals carry more weight than the long-run average.' if _gf_chg > 0.01 else 'The relationship between goals and points has been stable across eras.'}"
                        )
                        with st.expander("Formula: Weighted Least Squares", expanded=False):
                            st.latex(r"\hat{\beta}_{WLS} = (X^T W X)^{-1} X^T W y")
                            st.markdown(
                                "Where **W** is a diagonal matrix of season weights. "
                                f"Each season's weight = 0.85^(max_season − season_end), "
                                "so the most recent season has weight 1.0, the season before 0.85, two seasons back 0.72, and so on."
                            )

                st.divider()
                st.markdown("### Season Outcome Probability Estimator")
                st.markdown(
                    f"Based on every completed {selected_league} season in the selected range, "
                    "estimate the historical likelihood of different outcomes for a team on a given points total. "
                    "Drag the slider to run **what-if scenarios**."
                )
                _best_pred_prob = best_pred
                _prob_pts = st.slider(
                    "Projected final points",
                    min_value=20, max_value=110,
                    value=int(round(_best_pred_prob)),
                    step=1,
                    key="outcome_prob_slider",
                    help="Defaults to the model's predicted points. Drag to explore scenarios.",
                )
                _comp_hist = multi_season[multi_season["Season_End"] < CURRENT_SEASON_END].copy() if "Season_End" in multi_season.columns else multi_season.copy()
                if _comp_hist.empty:
                    _comp_hist = multi_season.copy()
                _n_teams_cfg = league_cfg["teams"]
                _rl_pos_prob = max(_n_teams_cfg - 2, 3) if _n_teams_cfg > 0 else 18
                _top_th = min(4, max(1, _n_teams_cfg // 5)) if _n_teams_cfg > 0 else 4
                _margin = max(5, int(len(_comp_hist) ** 0.45))
                _similar = _comp_hist[
                    (_comp_hist["Pts"] >= _prob_pts - _margin) &
                    (_comp_hist["Pts"] <= _prob_pts + _margin)
                ]
                if len(_similar) >= 3:
                    _n_sim = len(_similar)
                    _p_title = (_similar["Pos"] == 1).sum() / _n_sim * 100
                    _p_top = (_similar["Pos"] <= _top_th).sum() / _n_sim * 100
                    _p_rel = (_similar["Pos"] >= _rl_pos_prob).sum() / _n_sim * 100
                    _pc1, _pc2, _pc3, _pc4 = st.columns(4)
                    _pc1.metric("Title Won", f"{_p_title:.0f}%",
                                help=f"Of {_n_sim} hist. teams within ±{_margin} pts of {_prob_pts}")
                    _pc2.metric(f"Top {_top_th} Finish", f"{_p_top:.0f}%",
                                help=f"Based on {_n_sim} comparable historical seasons")
                    _pc3.metric("Relegation Risk", f"{_p_rel:.0f}%",
                                help=f"% of similar-points teams who were relegated")
                    _pc4.metric("Sample Seasons", str(_n_sim),
                                help="Historical team-seasons in the points bracket")
                    if _p_title > 50:
                        st.success(f"A team on **{_prob_pts} pts** has historically won the {selected_league} title **{_p_title:.0f}%** of the time. Dominant.")
                    elif _p_top > 65:
                        st.info(f"A team on **{_prob_pts} pts** has a **{_p_top:.0f}%** historical chance of a top-{_top_th} finish.")
                    elif _p_rel > 30:
                        st.warning(f"Caution: teams on **{_prob_pts} pts** have historically been relegated **{_p_rel:.0f}%** of the time.")
                    else:
                        st.info(f"A team on **{_prob_pts} pts** typically finishes as a solid mid-table side with no serious relegation concerns.")
                    with st.expander("How outcome probabilities are calculated"):
                        st.markdown(
                            f"We search all **{len(_comp_hist):,}** completed {selected_league} team-seasons in the selected range "
                            f"for teams whose final points total fell within **±{_margin} pts** of **{_prob_pts}**, "
                            f"finding **{_n_sim}** comparable historical seasons. "
                            "We count how many of those teams won the title, finished top "
                            f"{_top_th}, or were relegated — giving **empirical, assumption-free** probabilities. "
                            "The margin automatically scales with dataset size to ensure adequate sample sizes."
                        )
                else:
                    st.info(
                        f"Not enough comparable historical data near {_prob_pts} pts (fewer than 3 seasons). "
                        "Try expanding the season range in the sidebar to include more history."
                    )

            st.divider()

            st.markdown("### Key Insights from the Data")

            if not multi_season.empty:
                n_teams = league_cfg["teams"]
                relegation_cutoff = max(n_teams - 2, 3) if n_teams > 0 else 18
                games_per_season = league_cfg["games_per_season"]

                avg_champ_pts = multi_season[multi_season["Pos"] == 1]["Pts"].mean()
                avg_relegated_pts = multi_season[multi_season["Pos"] >= relegation_cutoff]["Pts"].mean()
                avg_top4_gd = multi_season[multi_season["Pos"] <= 4]["GD"].mean()
                avg_bottom_gd = multi_season[multi_season["Pos"] >= relegation_cutoff]["GD"].mean()

                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    st.metric("Avg. Champion Points", f"{avg_champ_pts:.1f}")
                    st.metric("Avg. Top 4 Goal Difference", f"+{avg_top4_gd:.1f}")
                with col_i2:
                    st.metric("Avg. Relegated Team Points", f"{avg_relegated_pts:.1f}")
                    st.metric(f"Avg. Bottom {n_teams - relegation_cutoff + 1} Goal Difference", f"{avg_bottom_gd:.1f}")

                st.divider()

                ppg_champ = avg_champ_pts / games_per_season if games_per_season > 0 else 0

                st.markdown("### Findings")
                st.markdown(f"""
1. **Goal difference is the strongest single predictor of league position.** Across {multi_season['Season_End'].nunique()} seasons, the Pearson correlation between GD and Pts is extremely high, confirming that balanced teams (strong attack + solid defense) finish highest.

2. **Defense matters as much as attack.** The regression coefficients for GF and GA are roughly symmetric in magnitude, indicating that preventing a goal is worth approximately the same as scoring one.

3. **The points threshold for survival is remarkably stable.** Relegated teams average ~{avg_relegated_pts:.0f} points, suggesting a practical survival target of roughly {avg_relegated_pts + 5:.0f} points per season.

4. **Champions typically require {avg_champ_pts:.0f}+ points.** The average title-winning total of {avg_champ_pts:.1f} points corresponds to roughly {ppg_champ:.2f} points per game over {games_per_season} matches.
                """)

            st.divider()
            st.caption(f"Data source: Wikipedia {selected_league} season articles. Statistical models are OLS regressions estimated via statsmodels.")

    with tab5:
        st.subheader("Penalty Analysis & Save Predictor")
        st.markdown(
            f"Penalty statistics scraped from Transfermarkt covering every player and goalkeeper "
            f"to have taken or faced a penalty in the {selected_league}. "
            "Use the predictor below to estimate the probability of a goalkeeper saving a penalty from a specific taker."
        )
        with st.expander("The goalkeeper movement rule — and why it matters", expanded=False):
            st.markdown(
                "**IFAB Law 14 (updated 2019/20):** At the moment of the kick, the goalkeeper must have "
                "**at least one foot on or in line with the goal line**. Previously, goalkeepers could stand "
                "anywhere on the line — or even step forward — before diving. The new rule (enforced via VAR) "
                "means penalties are retaken if the goalkeeper moves both feet off the line before contact.\n\n"
                "**Why this matters for analysis:**\n"
                "- **Save rates have dropped** since 2019/20 because goalkeepers can no longer gain an advantage "
                "by stepping forward (which cut down the angle and reaction time for the taker).\n"
                "- **Historical all-time save rates** (which include the pre-rule era) may overestimate "
                "a modern goalkeeper's ability to save penalties, since part of that record was accumulated "
                "under more lenient movement rules.\n"
                "- **Takers have become bolder** — knowing the goalkeeper is more constrained, some takers "
                "now favour power over placement, and down-the-middle penalties have increased.\n\n"
                "_This dashboard uses all-time records. When interpreting save rates for active goalkeepers, "
                "keep in mind that their recent record (post-2019) is a better indicator of current ability "
                "than their career-long average._"
            )

        SAVED_SHARE_OF_MISSES = 0.57
        OFF_TARGET_SHARE_OF_MISSES = 0.43

        st.subheader(f"Penalty Takers (All-Time {selected_league} Era)")
        st.markdown(
            f"Every player who has taken a penalty in the {selected_league} — "
            "including goalkeepers and defenders. Use the search box to find a specific player."
        )
        with st.spinner(f"Loading all-time penalty taker records ({league_cfg['start_year']}-present)..."):
            alltime_takers = load_alltime_taker_penalties(
                league_cfg["tm_slug"], league_cfg["tm_code"],
                league_cfg["start_year"], league_cfg["season_type"],
                is_cup=league_cfg.get("is_cup", False),
                league_name=selected_league,
            )

        if not alltime_takers.empty and "First_Season" in alltime_takers.columns and str(alltime_takers["First_Season"].iloc[0]) == "—":
            st.info("Live data from Transfermarkt is currently unavailable. Showing cached penalty statistics.")

        if not alltime_takers.empty:
            takers_full = alltime_takers.copy()
            takers_full["Est. Saved"] = (takers_full["Missed"] * SAVED_SHARE_OF_MISSES).round(0).astype(int)
            takers_full["Est. Off Target"] = takers_full["Missed"] - takers_full["Est. Saved"]
            takers_full["Saved %"] = np.where(
                takers_full["Penalties"] > 0,
                (takers_full["Est. Saved"] / takers_full["Penalties"] * 100).round(1),
                0.0,
            )
            takers_full["Off Target %"] = np.where(
                takers_full["Penalties"] > 0,
                (takers_full["Est. Off Target"] / takers_full["Penalties"] * 100).round(1),
                0.0,
            )

            @st.fragment
            def taker_search_fragment():
                taker_search = st.text_input("Search for a penalty taker", "", key="taker_search", placeholder="e.g. Shearer, Lampard, Salah, Van Dijk...")
                takers_sorted = takers_full.sort_values("Penalties", ascending=False).reset_index(drop=True)
                if taker_search.strip():
                    search_term = taker_search.strip().lower()
                    takers_sorted = takers_sorted[takers_sorted["Player"].str.lower().str.contains(search_term, na=False)]
                takers_sorted.index += 1
                st.markdown(f"**{len(takers_sorted)} taker{'s' if len(takers_sorted) != 1 else ''}** found.")
                table_height = min(500, max(80, 35 + len(takers_sorted) * 35))
                st.dataframe(takers_sorted, use_container_width=True, height=table_height)
                share_table_buttons(takers_sorted, f"{selected_league} Penalty Takers", "pen_takers")
            taker_search_fragment()

            st.caption(
                "\"Est. Saved\" and \"Est. Off Target\" are estimated from the \"Missed\" total using "
                "league-wide research (roughly 57% of missed penalties are saved by the goalkeeper, "
                "43% miss the target entirely including hitting the woodwork)."
            )
        else:
            st.warning("Could not load penalty taker records.")

        st.divider()

        st.subheader("Career Penalty Lookup (All Competitions)")
        st.markdown(
            "Search for any player by name to see their **entire career penalty record** across all top-flight "
            "competitions worldwide — including leagues, Champions League, Europa League, international matches, "
            "and domestic cups. Data sourced directly from Transfermarkt's individual player records."
        )

        @st.fragment
        def career_lookup_fragment():
            career_search = st.text_input(
                "Search for a player (career penalties)",
                "",
                key="career_pen_search",
                placeholder="e.g. Szoboszlai, Salah, Lewandowski, Messi..."
            )
            if career_search.strip():
                search_q = career_search.strip()
                with st.spinner(f"Searching Transfermarkt for '{search_q}'..."):
                    try:
                        search_results = search_player_transfermarkt(search_q)
                    except Exception:
                        search_results = []

                if not search_results:
                    st.warning(f"No players found for '{search_q}'. Try a different spelling or shorter name.")
                else:
                    player_options = {
                        f"{r['name']} (ID: {r['player_id']})": r for r in search_results[:10]
                    }
                    if len(player_options) == 1:
                        selected_key = list(player_options.keys())[0]
                    else:
                        selected_key = st.selectbox(
                            "Select player",
                            list(player_options.keys()),
                            key="career_player_select"
                        )

                    selected_player = player_options[selected_key]
                    with st.spinner(f"Loading career penalty data for {selected_player['name']}..."):
                        try:
                            career_df, total_scored = scrape_player_career_penalties(
                                selected_player["slug"], selected_player["player_id"]
                            )
                        except Exception:
                            career_df = pd.DataFrame()
                            total_scored = 0

                    if career_df.empty:
                        st.info(f"No penalty goals found for {selected_player['name']}. They may not have scored any career penalties.")
                    else:
                        st.success(f"**{selected_player['name']}** — **{total_scored}** career penalty goals scored across all competitions")

                        comp_counts = career_df["Competition"].value_counts().reset_index()
                        comp_counts.columns = ["Competition", "Penalties Scored"]
                        club_counts = career_df["Club"].value_counts().reset_index()
                        club_counts.columns = ["Club", "Penalties Scored"]

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**By Competition**")
                            st.dataframe(comp_counts, use_container_width=True, hide_index=True)
                        with c2:
                            st.markdown("**By Club/Country**")
                            st.dataframe(club_counts, use_container_width=True, hide_index=True)

                        gk_counts = career_df["Goalkeeper"].value_counts().reset_index()
                        gk_counts.columns = ["Goalkeeper", "Times Beaten"]
                        gk_counts = gk_counts[gk_counts["Goalkeeper"].str.strip().astype(bool)]
                        if not gk_counts.empty:
                            st.markdown("**Goalkeepers Beaten Most Often**")
                            st.dataframe(gk_counts.head(10), use_container_width=True, hide_index=True)

                        if len(comp_counts) > 1:
                            fig_comp = go.Figure(data=[
                                go.Bar(
                                    x=comp_counts["Competition"],
                                    y=comp_counts["Penalties Scored"],
                                    marker_color="#2ecc71"
                                )
                            ])
                            fig_comp.update_layout(
                                title=f"{selected_player['name']} — Penalty Goals by Competition",
                                xaxis_title="Competition",
                                yaxis_title="Penalties Scored",
                                height=350,
                                margin=dict(l=40, r=40, t=40, b=80),
                            )
                            st.plotly_chart(fig_comp, use_container_width=True)

                        season_counts = career_df["Season"].value_counts().sort_index().reset_index()
                        season_counts.columns = ["Season", "Penalties Scored"]
                        if len(season_counts) > 1:
                            fig_season = go.Figure(data=[
                                go.Bar(
                                    x=season_counts["Season"],
                                    y=season_counts["Penalties Scored"],
                                    marker_color="#3498db"
                                )
                            ])
                            fig_season.update_layout(
                                title=f"{selected_player['name']} — Penalty Goals by Season",
                                xaxis_title="Season",
                                yaxis_title="Penalties Scored",
                                height=350,
                                margin=dict(l=40, r=40, t=40, b=80),
                            )
                            st.plotly_chart(fig_season, use_container_width=True)

                        st.markdown("**Full Career Penalty Record (All Scored Penalties)**")
                        display_df = career_df.copy()
                        display_df.index = range(1, len(display_df) + 1)
                        st.dataframe(display_df, use_container_width=True, height=min(600, max(100, 35 + len(display_df) * 35)))

                        st.caption(
                            "This table shows all penalties **scored** (converted) by this player across their entire career "
                            "(all competitions including leagues, cups, and international matches). "
                            "Missed/saved penalties are not included as Transfermarkt only provides scored penalty details at the individual player level. "
                            "Data source: Transfermarkt individual player penalty records."
                        )

        career_lookup_fragment()

        st.divider()

        if league_cfg["has_gk_data"]:
            st.subheader(f"Goalkeeper Penalty Records (All-Time {selected_league} Era)")
            st.markdown(
                f"Every goalkeeper who has faced a penalty in the {selected_league}, "
                "sorted alphabetically. Use the search box to find a specific keeper."
            )
            with st.spinner(f"Loading all-time goalkeeper penalty records ({league_cfg['start_year']}-present)..."):
                alltime_gks = load_alltime_gk_penalties(
                    league_cfg["tm_slug"], league_cfg["tm_code"],
                    league_cfg["start_year"], league_cfg["season_type"],
                    is_cup=league_cfg.get("is_cup", False),
                    league_name=selected_league,
                )

            if not alltime_gks.empty:
                @st.fragment
                def gk_search_fragment():
                    gk_search = st.text_input("Search for a goalkeeper", "", key="gk_search", placeholder="e.g. Schmeichel, De Gea, Alisson...")
                    gks_sorted = alltime_gks.sort_values("Goalkeeper", ascending=True).reset_index(drop=True)
                    if gk_search.strip():
                        search_term = gk_search.strip().lower()
                        gks_sorted = gks_sorted[gks_sorted["Goalkeeper"].str.lower().str.contains(search_term, na=False)]
                    gks_sorted.index += 1
                    st.markdown(f"**{len(gks_sorted)} goalkeeper{'s' if len(gks_sorted) != 1 else ''}** found.")
                    table_height = min(500, max(80, 35 + len(gks_sorted) * 35))
                    st.dataframe(gks_sorted, use_container_width=True, height=table_height)
                    share_table_buttons(gks_sorted, f"{selected_league} Penalty GKs", "pen_gks")
                gk_search_fragment()
            else:
                st.warning("Could not load goalkeeper penalty records.")
                alltime_gks = pd.DataFrame()
        else:
            st.info(f"Goalkeeper penalty save data is not available for the {selected_league} on Transfermarkt.")
            alltime_gks = pd.DataFrame()

        st.divider()
        st.subheader("Shot Placement Analysis")
        st.info(
            "**Important: All directions are from the GOALKEEPER'S perspective** (i.e. as the keeper faces the striker). "
            "\"Left\" means the goalkeeper's left, \"Right\" means the goalkeeper's right. "
            "This makes it easy for the goalkeeper to know exactly where to dive."
        )
        st.markdown(
            "Based on published research on professional penalty kicks (aggregated from major European leagues "
            "and international tournaments), the table below shows where penalty takers typically aim and "
            "how often goalkeepers save shots in each zone."
        )

        zone_df = pd.DataFrame(ZONE_PROBS).T
        zone_df.index.name = "Zone"
        zone_df["Expected Goal %"] = (100 - zone_df["GK Save %"] * zone_df["Taker %"] / 100).round(1)
        st.dataframe(zone_df, use_container_width=True)

        st.markdown("**Visual: Goal Zones (Goalkeeper's Perspective — as the keeper faces the ball)**")
        fig_zones = go.Figure()
        zones_grid = [
            {"name": "Top-Left", "x0": 0, "x1": 2.44, "y0": 1.6, "y1": 2.44, "taker": 13.7, "save": 5.2},
            {"name": "Top-Centre", "x0": 2.44, "x1": 4.88, "y0": 1.6, "y1": 2.44, "taker": 5.5, "save": 12.0},
            {"name": "Top-Right", "x0": 4.88, "x1": 7.32, "y0": 1.6, "y1": 2.44, "taker": 14.0, "save": 4.8},
            {"name": "Mid-Left", "x0": 0, "x1": 2.44, "y0": 0.8, "y1": 1.6, "taker": 3.8, "save": 30.0},
            {"name": "Mid-Right", "x0": 4.88, "x1": 7.32, "y0": 0.8, "y1": 1.6, "taker": 3.7, "save": 28.0},
            {"name": "Bottom-Left", "x0": 0, "x1": 2.44, "y0": 0, "y1": 0.8, "taker": 25.2, "save": 18.5},
            {"name": "Bottom-Centre", "x0": 2.44, "x1": 4.88, "y0": 0, "y1": 0.8, "taker": 8.3, "save": 55.0},
            {"name": "Bottom-Right", "x0": 4.88, "x1": 7.32, "y0": 0, "y1": 0.8, "taker": 25.8, "save": 17.8},
        ]
        for z in zones_grid:
            color_val = z["save"] / 55.0
            r_c = int(46 + (231 - 46) * (1 - color_val))
            g_c = int(204 - 204 * (1 - color_val) * 0.3)
            b_c = int(113 + (76 - 113) * (1 - color_val))
            fig_zones.add_shape(
                type="rect", x0=z["x0"], x1=z["x1"], y0=z["y0"], y1=z["y1"],
                fillcolor=f"rgba({r_c},{g_c},{b_c},0.6)",
                line=dict(color="white", width=2),
            )
            fig_zones.add_annotation(
                x=(z["x0"] + z["x1"]) / 2, y=(z["y0"] + z["y1"]) / 2,
                text=f"<b>{z['name']}</b><br>Takers: {z['taker']}%<br>Save: {z['save']}%",
                showarrow=False, font=dict(size=11, color="white"),
            )
        fig_zones.add_annotation(
            x=1.22, y=-0.08, text="<b>GK's LEFT</b>",
            showarrow=False, font=dict(size=12, color="#3498db"),
        )
        fig_zones.add_annotation(
            x=6.1, y=-0.08, text="<b>GK's RIGHT</b>",
            showarrow=False, font=dict(size=12, color="#3498db"),
        )
        fig_zones.update_layout(
            xaxis=dict(range=[-0.3, 7.62], showgrid=False, zeroline=False, title="Width (m) — Goalkeeper's Perspective"),
            yaxis=dict(range=[-0.25, 2.6], showgrid=False, zeroline=False, title="Height (m)", scaleanchor="x"),
            height=380, margin=dict(l=40, r=40, t=20, b=50),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        fig_zones.add_shape(type="rect", x0=0, x1=7.32, y0=0, y1=2.44,
                            line=dict(color="white", width=3), fillcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_zones, use_container_width=True)

        st.markdown(
            "**Key insight:** Shots to the **top corners** are hardest to save (<6% save rate) "
            "but are riskier — more likely to miss the target entirely. "
            "**Bottom corners** are the most popular target (~51% of all penalties) with a moderate save rate (~18%). "
            "Shooting down the **centre** is surprisingly effective when the goalkeeper dives, "
            "but has the highest save rate (55%) when the keeper stays put."
        )

        st.divider()
        st.subheader("Penalty Save Probability Predictor")
        st.markdown(
            "Select a penalty taker and goalkeeper to estimate the probability of the penalty being scored or saved. "
            "The model combines the taker's conversion rate, the goalkeeper's save rate, and league-wide averages."
        )

        league_avg_conversion = 77.0
        league_avg_save = 17.0

        has_predictor_data = not alltime_takers.empty and not alltime_gks.empty and league_cfg["has_gk_data"]
        if has_predictor_data:
            taker_list = alltime_takers.sort_values("Penalties", ascending=False)["Player"].tolist()
            gk_list = alltime_gks.sort_values("Faced", ascending=False)["Goalkeeper"].tolist()

            @st.fragment
            def predictor_fragment():
                st.markdown("Select a taker and goalkeeper below — click the dropdown and **type to search** by name.")
                pred_col1, pred_col2 = st.columns(2)
                with pred_col1:
                    selected_taker = st.selectbox(f"Penalty Taker (all-time {selected_league} era)", taker_list, key="pen_taker")
                with pred_col2:
                    selected_gk = st.selectbox(f"Goalkeeper (all-time {selected_league} era)", gk_list, key="pen_gk")

                taker_row = alltime_takers[alltime_takers["Player"] == selected_taker].iloc[0]
                gk_row = alltime_gks[alltime_gks["Goalkeeper"] == selected_gk].iloc[0]

                taker_conv = taker_row["Conversion %"]
                taker_pens = taker_row["Penalties"]
                gk_save_rate = gk_row["Save %"]
                gk_faced = gk_row["Faced"]
                gk_club_display = gk_row.get("Clubs", gk_row.get("Club", ""))

                taker_weight = min(taker_pens / 10.0, 1.0)
                gk_weight = min(gk_faced / 10.0, 1.0)

                weighted_taker_conv = taker_weight * taker_conv + (1 - taker_weight) * league_avg_conversion
                weighted_gk_save = gk_weight * gk_save_rate + (1 - gk_weight) * league_avg_save

                p_goal = (weighted_taker_conv / 100) * (1 - weighted_gk_save / 200)
                p_save = (weighted_gk_save / 100) * (1 - weighted_taker_conv / 200)
                p_miss = max(0, 1 - p_goal - p_save)

                total = p_goal + p_save + p_miss
                p_goal /= total
                p_save /= total
                p_miss /= total

                taker_club_display = taker_row.get("Clubs", taker_row.get("Club", ""))
                st.markdown(f"**{selected_taker}** ({taker_club_display}) vs **{selected_gk}** ({gk_club_display})")

                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Goal Probability", f"{p_goal * 100:.1f}%")
                res_col2.metric("Save Probability", f"{p_save * 100:.1f}%")
                res_col3.metric("Miss Probability", f"{p_miss * 100:.1f}%")

                st.markdown("**Taker Profile**")
                taker_missed = int(taker_row["Missed"])
                taker_est_saved = round(taker_missed * SAVED_SHARE_OF_MISSES)
                taker_est_off_target = taker_missed - taker_est_saved
                saved_pct = (taker_est_saved / taker_pens * 100) if taker_pens > 0 else 0
                off_target_pct = (taker_est_off_target / taker_pens * 100) if taker_pens > 0 else 0

                t_col1, t_col2, t_col3 = st.columns(3)
                t_col1.metric("Penalties Taken", int(taker_pens))
                t_col2.metric("Scored", int(taker_row["Scored"]))
                t_col3.metric("Conversion Rate", f"{taker_conv:.1f}%")

                t_col4, t_col5, t_col6 = st.columns(3)
                t_col4.metric("Not Scored", taker_missed)
                t_col5.metric("Est. Saved by GK", f"{taker_est_saved} ({saved_pct:.0f}%)")
                t_col6.metric("Est. Off Target", f"{taker_est_off_target} ({off_target_pct:.0f}%)")

                st.markdown("**Goalkeeper Profile**")
                g_col1, g_col2, g_col3 = st.columns(3)
                g_col1.metric("Penalties Faced", int(gk_faced))
                g_col2.metric("Saved", int(gk_row["Saved"]))
                g_col3.metric("Save Rate", f"{gk_save_rate:.1f}%")

                with st.expander("How the prediction model works", expanded=False):
                    st.markdown(
                        "The model combines three data sources:\n\n"
                        "1. **Taker's conversion rate** — weighted by sample size. "
                        f"With {int(taker_pens)} penalties on record, the taker's stats are weighted "
                        f"at {taker_weight * 100:.0f}% vs the league average ({league_avg_conversion}%).\n\n"
                        "2. **Goalkeeper's save rate** — similarly weighted by number of penalties faced. "
                        f"With {int(gk_faced)} penalties faced, the keeper's stats are weighted "
                        f"at {gk_weight * 100:.0f}% vs the league average ({league_avg_save}%).\n\n"
                        "3. **Bayesian shrinkage** — players with fewer penalties are regressed toward "
                        "league averages to avoid overreacting to small samples. For example, a player "
                        "who scored 1 out of 1 (100%) is not truly a 100% converter."
                    )
                    st.latex(r"P(\text{goal}) = \text{Weighted Conversion} \times \left(1 - \frac{\text{Weighted Save Rate}}{2}\right)")
                    st.latex(r"P(\text{save}) = \text{Weighted Save Rate} \times \left(1 - \frac{\text{Weighted Conversion}}{2}\right)")
                    st.markdown("Probabilities are then normalised to sum to 100%.")

                st.divider()
                st.subheader("Goalkeeper Advice: Where to Dive")
                st.info(
                    "**Reminder: All directions below are from YOUR perspective as the goalkeeper** "
                    "(facing the penalty taker). \"Left\" = dive to your left, \"Right\" = dive to your right."
                )

                gk_reputation = weighted_gk_save / league_avg_save
                taker_skill = weighted_taker_conv / league_avg_conversion

                st.markdown("#### Naive Analysis (no strategic adjustment)")
                st.markdown(
                    "This assumes the taker shoots based on league-average placement — "
                    "i.e. they haven't studied this specific goalkeeper."
                )

                naive_data = []
                for zone, probs in ZONE_PROBS.items():
                    expected_saves = probs["Taker %"] * probs["GK Save %"] / 100
                    naive_data.append({
                        "Zone": zone,
                        "Taker Aims Here %": probs["Taker %"],
                        "GK Save Rate %": probs["GK Save %"],
                        "Expected Save Value": round(expected_saves, 2),
                    })
                naive_df = pd.DataFrame(naive_data).sort_values("Expected Save Value", ascending=False)
                naive_df.index = range(1, len(naive_df) + 1)
                st.dataframe(naive_df, use_container_width=True)

                naive_best = naive_df.iloc[0]["Zone"]

                st.divider()
                st.markdown("#### Game-Theory Adjusted Analysis")
                st.caption(
                    "_Adjustment model: heuristic shift toward preferred zones proportional to GK underperformance. "
                    "Adjusted taker probabilities assume reduced strategic diversification due to below-average GK performance, "
                    "or increased diversification against high-reputation goalkeepers._"
                )
                st.markdown(
                    f"Smart penalty takers do their homework. **{selected_gk}** has a "
                    f"{'high' if gk_reputation > 1.1 else 'average' if gk_reputation > 0.9 else 'below-average'} "
                    f"save rate ({gk_save_rate:.1f}% vs league avg {league_avg_save:.0f}%). "
                )
                if gk_reputation > 1.1:
                    st.markdown(
                        f"Because **{selected_gk}** is known as a strong penalty saver, "
                        f"**{selected_taker}** is more likely to adjust — avoiding the most "
                        f"predictable zones (bottom corners) and instead going for harder-to-save "
                        f"areas (top corners, centre). This shifts where the goalkeeper should expect the shot."
                    )
                elif gk_reputation < 0.9:
                    st.markdown(
                        f"Because **{selected_gk}** has a lower-than-average save rate, "
                        f"**{selected_taker}** is less likely to overthink placement and will "
                        f"probably stick to their preferred zones (typically bottom corners)."
                    )
                else:
                    st.markdown(
                        f"With an average save reputation, **{selected_taker}** will likely "
                        f"make moderate adjustments to their usual placement."
                    )

                adjusted_data = []
                for zone, probs in ZONE_PROBS.items():
                    base_taker_pct = probs["Taker %"]
                    is_easy_zone = zone.startswith("Bottom-") and zone != "Bottom-Centre"
                    is_hard_zone = zone.startswith("Top-") and zone != "Top-Centre"
                    is_centre = "Centre" in zone

                    shift_factor = (gk_reputation - 1.0) * taker_skill * 0.4

                    if is_easy_zone:
                        adj_taker_pct = base_taker_pct * (1 - shift_factor)
                    elif is_hard_zone:
                        adj_taker_pct = base_taker_pct * (1 + shift_factor * 1.2)
                    elif is_centre:
                        adj_taker_pct = base_taker_pct * (1 + shift_factor * 0.8)
                    else:
                        adj_taker_pct = base_taker_pct * (1 + shift_factor * 0.3)

                    adj_taker_pct = max(1.0, adj_taker_pct)
                    adjusted_data.append({
                        "Zone": zone,
                        "Base Taker %": base_taker_pct,
                        "Adjusted Taker %": round(adj_taker_pct, 1),
                        "Shift": f"{'+' if adj_taker_pct > base_taker_pct else ''}{adj_taker_pct - base_taker_pct:.1f}",
                        "GK Save Rate %": probs["GK Save %"],
                        "Adj. Expected Save": round(adj_taker_pct * probs["GK Save %"] / 100, 2),
                    })

                total_adj_pct = sum(d["Adjusted Taker %"] for d in adjusted_data)
                for d in adjusted_data:
                    d["Adjusted Taker %"] = round(d["Adjusted Taker %"] / total_adj_pct * 100, 1)
                    d["Adj. Expected Save"] = round(d["Adjusted Taker %"] * d["GK Save Rate %"] / 100, 2)

                adj_df = pd.DataFrame(adjusted_data).sort_values("Adj. Expected Save", ascending=False)
                adj_df.index = range(1, len(adj_df) + 1)
                st.dataframe(adj_df, use_container_width=True)

                st.caption(
                    "_Note: estimates are subject to sampling variability. "
                    "Confidence decreases for small sample sizes. "
                    "These probabilities are modelled approximations, not certainties._"
                )

                adj_best = adj_df.iloc[0]["Zone"]
                adj_best_value = adj_df.iloc[0]["Adj. Expected Save"]

                if adj_best != naive_best:
                    st.warning(
                        f"**Strategic shift detected!** Without adjustment, the best dive is **your {naive_best.lower()}**. "
                        f"But accounting for the taker's likely adjustment against this goalkeeper, "
                        f"the best dive shifts to **your {adj_best.lower()}** "
                        f"(adjusted expected save value: {adj_best_value:.2f})."
                    )
                    st.success(
                        f"**Final recommendation:** Dive to **your {adj_best.lower()}**. "
                        f"The taker is likely to adjust their placement because of your reputation, "
                        f"so anticipate the counter-adjustment rather than the naive expectation. "
                        f"Remember: this is YOUR left/right as the goalkeeper facing the striker."
                    )
                else:
                    st.success(
                        f"**Recommendation:** Dive to **your {adj_best.lower()}** "
                        f"(expected save value: {adj_best_value:.2f}). "
                        f"Even after accounting for the taker's likely strategic adjustment, "
                        f"this remains the best zone to cover. "
                        f"Remember: this is YOUR left/right as the goalkeeper facing the striker."
                    )

                st.divider()
                st.markdown("#### Expected Save Probability — Pitch Heatmap")
                st.caption("_Because penalties = spatial decision problem. Colour intensity shows where the goalkeeper is most likely to make a save._")

                zone_positions = {
                    "Top-Left":      (0.15, 0.85),
                    "Top-Centre":    (0.50, 0.85),
                    "Top-Right":     (0.85, 0.85),
                    "Mid-Left":      (0.15, 0.50),
                    "Mid-Right":     (0.85, 0.50),
                    "Bottom-Left":   (0.15, 0.15),
                    "Bottom-Centre": (0.50, 0.15),
                    "Bottom-Right":  (0.85, 0.15),
                }
                heatmap_zones = []
                for _, row in adj_df.iterrows():
                    z = row["Zone"]
                    if z in zone_positions:
                        x, y = zone_positions[z]
                        heatmap_zones.append({
                            "Zone": z, "x": x, "y": y,
                            "Save Prob": row["Adj. Expected Save"],
                            "GK Save %": row["GK Save Rate %"],
                            "Taker %": row["Adjusted Taker %"],
                        })

                fig_pitch = go.Figure()

                fig_pitch.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
                    line=dict(color="white", width=3), fillcolor="#2d6a2d", opacity=0.8)
                fig_pitch.add_shape(type="rect", x0=0.3, y0=-0.15, x1=0.7, y1=0,
                    line=dict(color="white", width=2))
                fig_pitch.add_shape(type="line", x0=0, y0=0, x1=1, y1=0,
                    line=dict(color="white", width=3))

                max_save = max(h["Save Prob"] for h in heatmap_zones) if heatmap_zones else 1
                for h in heatmap_zones:
                    intensity = h["Save Prob"] / max_save if max_save > 0 else 0
                    r = int(255 * intensity)
                    g = int(80 * (1 - intensity))
                    b = int(40 * (1 - intensity))
                    color = f"rgba({r},{g},{b},0.85)"

                    fig_pitch.add_trace(go.Scatter(
                        x=[h["x"]], y=[h["y"]],
                        mode="markers+text",
                        marker=dict(size=55, color=color, line=dict(color="white", width=2)),
                        text=f"{h['Save Prob']:.1f}%",
                        textposition="middle center",
                        textfont=dict(color="white", size=12, family="Arial Black"),
                        hovertemplate=(
                            f"<b>{h['Zone']}</b><br>"
                            f"Expected Save: {h['Save Prob']:.2f}%<br>"
                            f"GK Save Rate: {h['GK Save %']:.1f}%<br>"
                            f"Taker Aims Here: {h['Taker %']:.1f}%<extra></extra>"
                        ),
                        showlegend=False,
                    ))

                fig_pitch.update_layout(
                    template="plotly_dark",
                    height=350, width=500,
                    xaxis=dict(range=[-0.1, 1.1], showgrid=False, zeroline=False, showticklabels=False, title=""),
                    yaxis=dict(range=[-0.25, 1.15], showgrid=False, zeroline=False, showticklabels=False, title="", scaleanchor="x"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=20),
                    annotations=[
                        dict(x=0.5, y=1.1, text="Goal (from GK's perspective)", showarrow=False,
                             font=dict(size=13, color="white")),
                        dict(x=0.5, y=-0.2, text="Penalty Spot", showarrow=False,
                             font=dict(size=11, color="#aaa")),
                    ],
                )
                st.plotly_chart(fig_pitch, use_container_width=True)

                st.info(
                    "**Equilibrium insight:** In theory, optimal play converges toward mixed strategies. "
                    "Deviations arise when one player is perceived as weak — a strong GK forces takers to diversify, "
                    "while a weak GK allows takers to exploit their favourite zones. "
                    "The heatmap above visualises this spatial decision problem."
                )

                with st.expander("How the game-theory adjustment works", expanded=False):
                    st.markdown(
                        "**The strategic dilemma:** Penalty kicks are a classic game-theory scenario. "
                        "Both the taker and goalkeeper must commit to a direction before seeing what the other does.\n\n"
                        "**The adjustment logic:**\n"
                        f"1. **Goalkeeper reputation factor**: {selected_gk}'s weighted save rate "
                        f"({weighted_gk_save:.1f}%) is {gk_reputation:.2f}x the league average ({league_avg_save}%). "
                        f"{'A high reputation means takers will adjust more.' if gk_reputation > 1.1 else 'A normal reputation means moderate adjustment.'}\n\n"
                        f"2. **Taker skill factor**: {selected_taker}'s weighted conversion rate "
                        f"({weighted_taker_conv:.1f}%) is {taker_skill:.2f}x the league average ({league_avg_conversion}%). "
                        f"Skilled takers are better at adapting their placement.\n\n"
                        "3. **Shift mechanics**: Against a strong-saving GK, takers shift away from "
                        "bottom corners (easiest to save) toward top corners (hardest to save but riskier) "
                        "and sometimes down the centre (exploiting the keeper's tendency to dive). "
                        "The shift magnitude depends on both the GK's reputation and the taker's skill level.\n\n"
                        "4. **Result**: The adjusted zone probabilities show where a strategic taker is "
                        "actually likely to aim, which may differ significantly from league averages.\n\n"
                        "5. **Modern rule constraint (IFAB 2019/20)**: Goalkeepers must keep at least one foot "
                        "on the goal line at the moment of the kick. This limits the GK's ability to close down "
                        "the angle by stepping forward, making saves harder than in the pre-rule era. "
                        "All-time save rates may therefore slightly overestimate a goalkeeper's current saving ability."
                    )

            predictor_fragment()
        else:
            if alltime_takers.empty:
                st.warning("Penalty taker data could not be loaded.")
            if not league_cfg["has_gk_data"]:
                st.info(f"Goalkeeper penalty data is not available for the {selected_league}. The predictor requires both taker and goalkeeper data.")
            elif alltime_gks.empty:
                st.warning("Goalkeeper save data could not be loaded.")

        st.divider()
        st.caption(f"Penalty data source: Transfermarkt ({selected_league}). Shot placement research data aggregated from academic studies on professional penalty kicks.")

    if has_league_tables:
        with tab6:
            st.subheader(f"Team Insights — {selected_league}")
            st.markdown(
                "Select a team to see a personalised performance profile with historical trends, "
                "peer benchmarking, and data-driven recommendations for improving their chances of winning the title."
            )

            if rebased_seasons:
                n_rb_seasons = len(set(rebased_seasons))
                detail_parts = []
                for orig_pld, seasons in sorted(rebased_detail.items()):
                    detail_parts.append(f"{len(seasons)} season(s) originally had {orig_pld} games: {', '.join(seasons)}")
                detail_str = "; ".join(detail_parts) if detail_parts else f"{n_rb_seasons} season(s)"
                st.caption(
                    f"Note: {detail_str} — all rebased to the current {league_cfg['games_per_season']}-game standard for fair comparison."
                )

            if not multi_season.empty and "Squad" in multi_season.columns and selected_team is not None:
                n_teams = league_cfg["teams"]
                games_per_season = league_cfg["games_per_season"]

                team_data = multi_season[multi_season["Squad"] == selected_team].copy()
                team_data = team_data.sort_values("Season_End")

                if team_data.empty:
                    st.warning(f"No historical data found for {selected_team}.")
                else:
                    n_seasons = len(team_data)
                    latest = team_data.iloc[-1]
                    latest_season = latest["Season"]

                    st.markdown(f"### {selected_team} — Overview")

                    latest_pld = int(latest["Pld"]) if "Pld" in latest.index else games_per_season
                    season_complete = latest_pld >= games_per_season if games_per_season > 0 else True
                    completed_team_data = team_data[team_data["Pld"] >= games_per_season] if "Pld" in team_data.columns and games_per_season > 0 else team_data
                    completed_multi = multi_season[multi_season["Pld"] >= games_per_season] if "Pld" in multi_season.columns and games_per_season > 0 else multi_season

                    if not season_complete:
                        st.info(
                            f"The **{latest_season}** season is still in progress ({latest_pld} of {games_per_season} games played). "
                            f"Benchmarking and recommendations use completed seasons only for fair comparison."
                        )

                    st.markdown(f"**{n_seasons} seasons** of data in the {selected_league} (from the multi-season range selected in the sidebar).")

                    bench_data = completed_team_data if not completed_team_data.empty else team_data
                    bench_multi = completed_multi if not completed_multi.empty else multi_season

                    avg_pts = bench_data["Pts"].mean()
                    avg_pos = bench_data["Pos"].mean()
                    avg_gf = bench_data["GF"].mean() if "GF" in bench_data.columns else 0
                    avg_ga = bench_data["GA"].mean() if "GA" in bench_data.columns else 0
                    avg_gd = bench_data["GD"].mean() if "GD" in bench_data.columns else 0
                    avg_d = bench_data["D"].mean() if "D" in bench_data.columns else 0
                    best_pos = int(team_data["Pos"].min())
                    worst_pos = int(team_data["Pos"].max())
                    titles = int((team_data["Pos"] == 1).sum())
                    top_threshold = min(4, max(1, n_teams // 3)) if n_teams > 0 else 4
                    relegation_spots = max(1, round(n_teams * 0.15)) if n_teams > 0 else 3
                    relegation_pos = n_teams - relegation_spots + 1 if n_teams > 0 else 18
                    top_finishes = int((team_data["Pos"] <= top_threshold).sum())

                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    kpi1.metric("Avg. Points", f"{avg_pts:.1f}")
                    kpi2.metric("Avg. Position", f"{avg_pos:.1f}")
                    kpi3.metric("Titles Won", titles)
                    kpi4.metric(f"Top {top_threshold} Finishes", top_finishes)

                    kpi5, kpi6, kpi7, kpi8 = st.columns(4)
                    kpi5.metric("Best Finish", f"{best_pos}")
                    kpi6.metric("Worst Finish", f"{worst_pos}")
                    kpi7.metric("Avg. GF/Season", f"{avg_gf:.1f}")
                    kpi8.metric("Avg. GA/Season", f"{avg_ga:.1f}")

                    st.divider()
                    st.markdown("### Goal Sources & Top Scorers")
                    st.markdown(
                        f"Who scores the goals for **{selected_team}** and how? "
                        f"Breakdown of goal types for the **{latest_season}** season."
                    )

                    tm_season_id = int(season) - 1 if league_cfg["season_type"] == "split" else int(season)
                    with st.spinner("Loading scorer data from Transfermarkt..."):
                        scorers_df = scrape_top_scorers(
                            league_cfg["tm_slug"], league_cfg["tm_code"],
                            tm_season_id, is_cup=league_cfg["is_cup"]
                        )

                    if not scorers_df.empty:
                        team_name_lower = selected_team.lower().replace(" fc", "").replace("fc ", "").strip()
                        team_scorers = scorers_df[
                            scorers_df["Club"].str.lower().str.contains(team_name_lower, na=False) |
                            scorers_df["Club"].str.lower().apply(
                                lambda x: team_name_lower.split()[0] in x if team_name_lower else False
                            )
                        ].copy()

                        if team_scorers.empty:
                            team_words = team_name_lower.split()
                            for word in team_words:
                                if len(word) > 3:
                                    team_scorers = scorers_df[
                                        scorers_df["Club"].str.lower().str.contains(word, na=False)
                                    ].copy()
                                    if not team_scorers.empty:
                                        break

                        if not team_scorers.empty:
                            team_total_goals = team_scorers["Goals"].sum()
                            team_pen_goals = team_scorers["Pen. Goals"].sum()
                            team_open_play = team_scorers["Open Play Goals"].sum()
                            top_scorer = team_scorers.iloc[0]

                            gs1, gs2, gs3, gs4 = st.columns(4)
                            gs1.metric("Total Goals (Scorers)", team_total_goals)
                            gs2.metric("From Open Play", f"{team_open_play} ({team_open_play/max(1,team_total_goals)*100:.0f}%)")
                            gs3.metric("From Penalties", f"{team_pen_goals} ({team_pen_goals/max(1,team_total_goals)*100:.0f}%)")
                            gs4.metric("Top Scorer", f"{top_scorer['Player']} ({top_scorer['Goals']})")

                            if len(team_scorers) > 1:
                                top5 = team_scorers.head(8)
                                fig_scorers = go.Figure()
                                fig_scorers.add_trace(go.Bar(
                                    y=top5["Player"], x=top5["Open Play Goals"],
                                    name="Open Play", orientation="h",
                                    marker_color="#2ecc71",
                                ))
                                fig_scorers.add_trace(go.Bar(
                                    y=top5["Player"], x=top5["Pen. Goals"],
                                    name="Penalties", orientation="h",
                                    marker_color="#e74c3c",
                                ))
                                fig_scorers.update_layout(
                                    title=f"{selected_team} Goal Scorers ({latest_season})",
                                    xaxis_title="Goals", barmode="stack",
                                    height=max(250, len(top5) * 40 + 100),
                                    margin=dict(l=150, r=40, t=40, b=40),
                                    yaxis=dict(autorange="reversed"),
                                )
                                st.plotly_chart(fig_scorers, use_container_width=True)

                            goal_concentration = top_scorer["Goals"] / max(1, team_total_goals) * 100
                            pen_reliance = team_pen_goals / max(1, team_total_goals) * 100
                            n_scorers = len(team_scorers)

                            insights = []
                            if goal_concentration > 40:
                                insights.append(
                                    f"**High dependency on one player** — {top_scorer['Player']} scores "
                                    f"{goal_concentration:.0f}% of all goals. If this player gets injured or "
                                    f"loses form, the team's output could collapse. Developing alternative "
                                    f"goal threats (a second striker, goals from midfield, or set-piece specialists) is critical."
                                )
                            elif goal_concentration < 20 and n_scorers >= 5:
                                insights.append(
                                    f"**Well-distributed goals** — {n_scorers} different scorers with no single "
                                    f"player above {goal_concentration:.0f}%. This is a strength: the team isn't "
                                    f"dependent on any one individual and is harder for opponents to game-plan against."
                                )

                            if pen_reliance > 20:
                                insights.append(
                                    f"**Strong penalty-area threat** — {pen_reliance:.0f}% of goals come from penalties "
                                    f"({team_pen_goals} of {team_total_goals}). This shows the team is dangerous in the box "
                                    f"and forces opponents into fouls. To build on this, adding more open-play goal routes "
                                    f"(better crossing, through-balls, movement in the box) would make the attack even harder to defend against."
                                )
                            elif pen_reliance < 5 and team_total_goals > 20:
                                insights.append(
                                    f"**Diverse attack** — only {pen_reliance:.0f}% of goals from penalties. "
                                    f"The vast majority of output comes from open play and set-piece routines, "
                                    f"showing strong creative quality across the squad."
                                )

                            position_goals = {}
                            for _, row_s in team_scorers.iterrows():
                                pos = row_s["Position"]
                                if not pos:
                                    pos = "Unknown"
                                pos_cat = "Forward"
                                pos_lower = pos.lower()
                                if any(w in pos_lower for w in ["back", "defender", "defence"]):
                                    pos_cat = "Defender"
                                elif any(w in pos_lower for w in ["midfield", "midfielder"]):
                                    pos_cat = "Midfielder"
                                elif any(w in pos_lower for w in ["keeper", "goal"]):
                                    pos_cat = "Goalkeeper"
                                elif any(w in pos_lower for w in ["forward", "striker", "winger", "wing", "attack"]):
                                    pos_cat = "Forward"
                                position_goals[pos_cat] = position_goals.get(pos_cat, 0) + row_s["Goals"]

                            if position_goals and team_total_goals > 0:
                                fig_pos_goals = go.Figure(data=[go.Pie(
                                    labels=list(position_goals.keys()),
                                    values=list(position_goals.values()),
                                    hole=0.4,
                                    marker_colors=["#2ecc71", "#3498db", "#e74c3c", "#f39c12"],
                                )])
                                fig_pos_goals.update_layout(
                                    title="Goals by Position Group",
                                    height=300, margin=dict(l=20, r=20, t=40, b=20),
                                )
                                st.plotly_chart(fig_pos_goals, use_container_width=True)

                                fwd_pct = position_goals.get("Forward", 0) / team_total_goals * 100
                                mid_pct = position_goals.get("Midfielder", 0) / team_total_goals * 100
                                def_pct = position_goals.get("Defender", 0) / team_total_goals * 100

                                if mid_pct > 30:
                                    insights.append(
                                        f"**Goals from midfield ({mid_pct:.0f}%)** — a sign of a well-functioning "
                                        f"midfield unit that gets into scoring positions. Attacking midfielders and "
                                        f"box-to-box runners are contributing beyond just creating chances."
                                    )
                                elif mid_pct < 10 and team_total_goals > 15:
                                    insights.append(
                                        f"**Midfield not chipping in ({mid_pct:.0f}% of goals)** — almost all goals "
                                        f"come from forwards. Encouraging midfielders to arrive late in the box, take "
                                        f"more shots from the edge of the area, or get on the end of set pieces "
                                        f"would add a valuable extra dimension to the attack."
                                    )

                                if def_pct > 10:
                                    insights.append(
                                        f"**Defenders contributing goals ({def_pct:.0f}%)** — goals from centre-backs "
                                        f"and full-backs (often from corners, free kicks, and overlapping runs) add a "
                                        f"valuable source that opponents struggle to defend against."
                                    )

                            if insights:
                                st.markdown("**Goal Source Analysis:**")
                                for ins in insights:
                                    st.markdown(f"- {ins}")

                            st.markdown(f"**{selected_team} Scorers ({latest_season}):**")
                            display_scorers = team_scorers[["Player", "Position", "Goals", "Pen. Goals", "Open Play Goals", "Assists"]].copy()
                            display_scorers.index = range(1, len(display_scorers) + 1)
                            st.dataframe(display_scorers, use_container_width=True)

                            st.divider()
                            st.markdown("### Assist Sources — Wagon Wheel")
                            st.markdown(
                                f"Where do **{selected_team}**'s assists come from? "
                                f"This shows which players and positions create chances for the **{latest_season}** season."
                            )
                            with st.spinner("Loading assist data from Transfermarkt..."):
                                assists_df = scrape_top_assists(
                                    league_cfg["tm_slug"], league_cfg["tm_code"],
                                    tm_season_id, is_cup=league_cfg["is_cup"]
                                )
                            if not assists_df.empty:
                                team_assists = assists_df[
                                    assists_df["Club"].str.lower().str.contains(team_name_lower, na=False) |
                                    assists_df["Club"].str.lower().apply(
                                        lambda x: team_name_lower.split()[0] in x if team_name_lower else False
                                    )
                                ].copy()
                                if team_assists.empty:
                                    team_words = team_name_lower.split()
                                    for word in team_words:
                                        if len(word) > 3:
                                            team_assists = assists_df[
                                                assists_df["Club"].str.lower().str.contains(word, na=False)
                                            ].copy()
                                            if not team_assists.empty:
                                                break

                                if not team_assists.empty:
                                    def _pos_category(pos):
                                        pos_lower = pos.lower() if pos else ""
                                        if any(w in pos_lower for w in ["back", "defender", "defence"]):
                                            return "Defender"
                                        elif any(w in pos_lower for w in ["midfield", "midfielder"]):
                                            return "Midfielder"
                                        elif any(w in pos_lower for w in ["keeper", "goal"]):
                                            return "Goalkeeper"
                                        elif any(w in pos_lower for w in ["forward", "striker", "winger", "wing", "attack"]):
                                            return "Forward"
                                        return "Other"

                                    team_assists["Pos_Group"] = team_assists["Position"].apply(_pos_category)
                                    total_assists = team_assists["Assists"].sum()

                                    pos_colors = {"Defender": "#3498db", "Midfielder": "#2ecc71", "Forward": "#e74c3c", "Goalkeeper": "#f39c12", "Other": "#95a5a6"}
                                    pos_order = ["Defender", "Midfielder", "Forward", "Goalkeeper", "Other"]
                                    present_groups = [p for p in pos_order if p in team_assists["Pos_Group"].values]

                                    wagon_players = []
                                    wagon_assists = []
                                    wagon_colors = []
                                    wagon_positions = []
                                    for pg in present_groups:
                                        grp = team_assists[team_assists["Pos_Group"] == pg].sort_values("Assists", ascending=False)
                                        for _, r in grp.iterrows():
                                            wagon_players.append(r["Player"])
                                            wagon_assists.append(r["Assists"])
                                            wagon_colors.append(pos_colors.get(pg, "#95a5a6"))
                                            wagon_positions.append(pg)

                                    fig_wagon = go.Figure()
                                    fig_wagon.add_trace(go.Barpolar(
                                        r=wagon_assists,
                                        theta=wagon_players,
                                        marker_color=wagon_colors,
                                        marker_line_color="#fff",
                                        marker_line_width=1,
                                        opacity=0.85,
                                        hovertemplate="<b>%{theta}</b><br>Assists: %{r}<extra></extra>",
                                    ))
                                    fig_wagon.update_layout(
                                        title=f"{selected_team} Assist Sources ({latest_season})",
                                        polar=dict(
                                            radialaxis=dict(visible=True, showticklabels=True, tickfont=dict(size=10)),
                                            angularaxis=dict(tickfont=dict(size=9)),
                                        ),
                                        height=max(450, len(wagon_players) * 25 + 150),
                                        margin=dict(l=80, r=80, t=50, b=50),
                                        showlegend=False,
                                    )
                                    st.plotly_chart(fig_wagon, use_container_width=True)

                                    legend_html = " &nbsp; ".join(
                                        f'<span style="display:inline-block;width:12px;height:12px;background:{pos_colors[pg]};border-radius:2px;margin-right:4px;vertical-align:middle;"></span>{pg}'
                                        for pg in present_groups
                                    )
                                    st.markdown(legend_html, unsafe_allow_html=True)

                                    pos_assist_totals = team_assists.groupby("Pos_Group")["Assists"].sum()
                                    aw1, aw2 = st.columns(2)
                                    with aw1:
                                        fig_pos_assists = go.Figure(data=[go.Pie(
                                            labels=[p for p in pos_order if p in pos_assist_totals.index],
                                            values=[pos_assist_totals[p] for p in pos_order if p in pos_assist_totals.index],
                                            hole=0.4,
                                            marker_colors=[pos_colors[p] for p in pos_order if p in pos_assist_totals.index],
                                        )])
                                        fig_pos_assists.update_layout(
                                            title="Assists by Position Group",
                                            height=300, margin=dict(l=20, r=20, t=40, b=20),
                                        )
                                        st.plotly_chart(fig_pos_assists, use_container_width=True)
                                    with aw2:
                                        top_assisters = team_assists.head(8)
                                        fig_assist_bar = go.Figure()
                                        fig_assist_bar.add_trace(go.Bar(
                                            y=top_assisters["Player"], x=top_assisters["Assists"],
                                            orientation="h",
                                            marker_color=[pos_colors.get(pg, "#95a5a6") for pg in top_assisters["Pos_Group"]],
                                        ))
                                        fig_assist_bar.update_layout(
                                            title=f"Top Assist Providers",
                                            xaxis_title="Assists",
                                            height=300,
                                            margin=dict(l=120, r=20, t=40, b=20),
                                            yaxis=dict(autorange="reversed"),
                                        )
                                        st.plotly_chart(fig_assist_bar, use_container_width=True)

                                    assist_insights = []
                                    top_assister = team_assists.iloc[0]
                                    top_assister_pct = top_assister["Assists"] / max(1, total_assists) * 100
                                    if top_assister_pct > 30:
                                        assist_insights.append(
                                            f"**Creative hub** — {top_assister['Player']} provides {top_assister_pct:.0f}% of all assists "
                                            f"({top_assister['Assists']} of {total_assists}). The team's chance creation flows heavily through this player."
                                        )
                                    mid_assists = pos_assist_totals.get("Midfielder", 0)
                                    mid_assist_pct = mid_assists / max(1, total_assists) * 100
                                    def_assists = pos_assist_totals.get("Defender", 0)
                                    def_assist_pct = def_assists / max(1, total_assists) * 100
                                    fwd_assists = pos_assist_totals.get("Forward", 0)
                                    fwd_assist_pct = fwd_assists / max(1, total_assists) * 100
                                    if def_assist_pct > 25:
                                        assist_insights.append(
                                            f"**Defenders as playmakers ({def_assist_pct:.0f}% of assists)** — full-backs and "
                                            f"centre-backs are major creative outlets, likely through overlapping runs, crosses, and long-range passing."
                                        )
                                    if fwd_assist_pct > 30:
                                        assist_insights.append(
                                            f"**Forwards creating for each other ({fwd_assist_pct:.0f}%)** — wingers and strikers "
                                            f"are combining effectively, suggesting good movement and interplay in the final third."
                                        )
                                    n_assisters = len(team_assists)
                                    if n_assisters >= 8 and top_assister_pct < 25:
                                        assist_insights.append(
                                            f"**Spread creativity** — {n_assisters} different players have provided assists with no single "
                                            f"player dominating. This makes the team harder to shut down tactically."
                                        )

                                    if assist_insights:
                                        st.markdown("**Assist Analysis:**")
                                        for ai in assist_insights:
                                            st.markdown(f"- {ai}")

                                    st.markdown(f"**{selected_team} Assist Providers ({latest_season}):**")
                                    display_assists = team_assists[["Player", "Position", "Appearances", "Assists"]].copy()
                                    display_assists.index = range(1, len(display_assists) + 1)
                                    st.dataframe(display_assists, use_container_width=True)
                                else:
                                    st.info(f"Could not match {selected_team} in the assist data.")
                            else:
                                st.info(f"Assist data for the {latest_season} season could not be loaded from Transfermarkt.")
                        else:
                            st.info(f"Could not match {selected_team} in the scorer data. Team name matching between data sources may differ.")
                    else:
                        st.info(f"Top scorer data for the {latest_season} season could not be loaded from Transfermarkt.")

                    st.divider()
                    st.markdown("### Historical Trends")

                    if "PPG" in team_data.columns and len(team_data) > 1:
                        league_avg_ppg = bench_multi.groupby("Season_End")["PPG"].mean().reset_index()
                        league_avg_ppg.columns = ["Season_End", "League_Avg_PPG"]
                        team_trend = team_data.merge(league_avg_ppg, on="Season_End", how="left")

                        fig_ppg = go.Figure()
                        fig_ppg.add_trace(go.Scatter(
                            x=team_trend["Season"], y=team_trend["PPG"],
                            mode="lines+markers", name=selected_team,
                            line=dict(color="#2ecc71", width=3),
                        ))
                        fig_ppg.add_trace(go.Scatter(
                            x=team_trend["Season"], y=team_trend["League_Avg_PPG"],
                            mode="lines", name="League Average",
                            line=dict(color="#95a5a6", width=2, dash="dash"),
                        ))
                        fig_ppg.update_layout(
                            title="Points Per Game Over Time",
                            xaxis_title="Season", yaxis_title="PPG",
                            height=380, margin=dict(l=40, r=40, t=40, b=60),
                        )
                        st.plotly_chart(fig_ppg, use_container_width=True)

                    if "GF" in team_data.columns and "GA" in team_data.columns and len(team_data) > 1:
                        fig_goals = go.Figure()
                        fig_goals.add_trace(go.Bar(
                            x=team_data["Season"], y=team_data["GF"],
                            name="Goals Scored", marker_color="#2ecc71",
                        ))
                        fig_goals.add_trace(go.Bar(
                            x=team_data["Season"], y=-team_data["GA"],
                            name="Goals Conceded", marker_color="#e74c3c",
                        ))
                        fig_goals.update_layout(
                            title="Goals Scored vs Conceded",
                            xaxis_title="Season", yaxis_title="Goals",
                            barmode="relative", height=380,
                            margin=dict(l=40, r=40, t=40, b=60),
                        )
                        st.plotly_chart(fig_goals, use_container_width=True)

                    if len(team_data) > 1:
                        fig_pos = go.Figure()
                        fig_pos.add_trace(go.Scatter(
                            x=team_data["Season"], y=team_data["Pos"],
                            mode="lines+markers", name="League Position",
                            line=dict(color="#3498db", width=3),
                        ))
                        fig_pos.update_layout(
                            title="League Position Over Time",
                            xaxis_title="Season", yaxis_title="Position",
                            yaxis=dict(autorange="reversed"),
                            height=350, margin=dict(l=40, r=40, t=40, b=60),
                        )
                        st.plotly_chart(fig_pos, use_container_width=True)

                    st.divider()
                    st.markdown("### Peer Benchmarking")

                    league_season_avg = bench_multi.groupby("Season_End").agg(
                        Avg_Pts=("Pts", "mean"),
                        Avg_GF=("GF", "mean") if "GF" in bench_multi.columns else ("Pts", "mean"),
                        Avg_GA=("GA", "mean") if "GA" in bench_multi.columns else ("Pts", "mean"),
                        Avg_GD=("GD", "mean") if "GD" in bench_multi.columns else ("Pts", "mean"),
                    ).reset_index()

                    top4_avg = bench_multi[bench_multi["Pos"] <= top_threshold].groupby("Season_End").agg(
                        Top4_Pts=("Pts", "mean"),
                    ).reset_index()

                    champ_avg = bench_multi[bench_multi["Pos"] == 1].groupby("Season_End").agg(
                        Champ_Pts=("Pts", "mean"),
                    ).reset_index()

                    compare_source = completed_team_data if not completed_team_data.empty else team_data
                    compare = compare_source[["Season", "Season_End", "Pts", "Pos"]].merge(
                        league_season_avg, on="Season_End", how="left"
                    ).merge(top4_avg, on="Season_End", how="left").merge(
                        champ_avg, on="Season_End", how="left"
                    )

                    if not compare.empty:
                        latest_comp = compare.iloc[-1]
                        bench_season_label = latest_comp["Season"]
                        diff_avg = latest_comp["Pts"] - latest_comp["Avg_Pts"]
                        diff_top4 = latest_comp["Pts"] - latest_comp.get("Top4_Pts", latest_comp["Pts"])
                        diff_champ = latest_comp["Pts"] - latest_comp.get("Champ_Pts", latest_comp["Pts"])

                        bc1, bc2, bc3 = st.columns(3)
                        bc1.metric(
                            f"vs League Avg ({bench_season_label})",
                            f"{latest_comp['Pts']:.0f} pts",
                            f"{diff_avg:+.1f}",
                        )
                        bc2.metric(
                            f"vs Top {top_threshold} Avg ({bench_season_label})",
                            f"{latest_comp.get('Top4_Pts', 0):.0f} pts target",
                            f"{diff_top4:+.1f}",
                        )
                        bc3.metric(
                            f"vs Champion ({bench_season_label})",
                            f"{latest_comp.get('Champ_Pts', 0):.0f} pts target",
                            f"{diff_champ:+.1f}",
                        )

                    st.divider()
                    st.markdown("### Trophy Target Analysis")
                    st.markdown(
                        "Based on historical data, these are the typical points thresholds "
                        f"needed to achieve each target in the {selected_league}."
                    )

                    hist_champ_pts = bench_multi[bench_multi["Pos"] == 1]["Pts"]
                    hist_top_pts = bench_multi[bench_multi["Pos"] <= top_threshold]["Pts"]
                    hist_survival_pts = bench_multi[bench_multi["Pos"] < relegation_pos]["Pts"]
                    hist_relegated_pts = bench_multi[bench_multi["Pos"] >= relegation_pos]["Pts"]

                    if not hist_champ_pts.empty:
                        tgt1, tgt2, tgt3 = st.columns(3)
                        tgt1.metric("Title Target", f"{hist_champ_pts.mean():.0f} pts", f"Range: {hist_champ_pts.min():.0f}–{hist_champ_pts.max():.0f}")
                        tgt2.metric(f"Top {top_threshold} Target", f"{hist_top_pts.quantile(0.5):.0f} pts", f"75th pct: {hist_top_pts.quantile(0.75):.0f}")
                        if not hist_relegated_pts.empty:
                            tgt3.metric("Survival Floor", f"{hist_relegated_pts.max():.0f} pts", f"Avg relegated: {hist_relegated_pts.mean():.0f}")

                    league_avg_gf_val = bench_multi["GF"].mean() if "GF" in bench_multi.columns else 0
                    league_avg_ga_val = bench_multi["GA"].mean() if "GA" in bench_multi.columns else 0
                    league_avg_d = bench_multi["D"].mean() if "D" in bench_multi.columns else 0

                    st.divider()
                    st.markdown("### Strengths & Weaknesses")

                    has_wdl = "W" in team_data.columns and "D" in team_data.columns and "L" in team_data.columns
                    has_goals = "GF" in team_data.columns and "GA" in team_data.columns

                    champ_data = bench_multi[bench_multi["Pos"] == 1]
                    top_n_data = bench_multi[bench_multi["Pos"] <= top_threshold]
                    champ_avg_gf = champ_data["GF"].mean() if has_goals and not champ_data.empty else 0
                    champ_avg_ga = champ_data["GA"].mean() if has_goals and not champ_data.empty else 0
                    champ_avg_w = champ_data["W"].mean() if has_wdl and not champ_data.empty else 0
                    champ_avg_d = champ_data["D"].mean() if has_wdl and not champ_data.empty else 0
                    champ_avg_l = champ_data["L"].mean() if has_wdl and not champ_data.empty else 0
                    top_n_avg_gf = top_n_data["GF"].mean() if has_goals and not top_n_data.empty else 0
                    top_n_avg_ga = top_n_data["GA"].mean() if has_goals and not top_n_data.empty else 0

                    if has_wdl:
                        avg_w = bench_data["W"].mean()
                        league_avg_w = bench_multi["W"].mean()
                        league_avg_l = bench_multi["L"].mean()
                        avg_l = bench_data["L"].mean()

                    strengths = []
                    weaknesses = []

                    gf_per_game = avg_gf / games_per_season if games_per_season > 0 else 0
                    ga_per_game = avg_ga / games_per_season if games_per_season > 0 else 0
                    league_gf_pg = league_avg_gf_val / games_per_season if games_per_season > 0 else 0
                    league_ga_pg = league_avg_ga_val / games_per_season if games_per_season > 0 else 0
                    champ_gf_pg = champ_avg_gf / games_per_season if games_per_season > 0 else 0
                    champ_ga_pg = champ_avg_ga / games_per_season if games_per_season > 0 else 0

                    if has_goals:
                        gf_diff = avg_gf - league_avg_gf_val
                        ga_diff = avg_ga - league_avg_ga_val
                        gf_vs_champ = avg_gf - champ_avg_gf
                        ga_vs_champ = avg_ga - champ_avg_ga

                        if avg_gf > league_avg_gf_val * 1.15:
                            if avg_gf >= champ_avg_gf * 0.95:
                                strengths.append(
                                    f"**Elite attack** — scoring {gf_per_game:.2f} goals/game ({avg_gf:.1f}/season), "
                                    f"on par with title-winning teams ({champ_gf_pg:.2f}/game). "
                                    f"The forward line and creative midfield are performing at the highest level."
                                )
                            else:
                                strengths.append(
                                    f"**Above-average attack** — scoring {gf_per_game:.2f} goals/game ({avg_gf:.1f}/season), "
                                    f"+{gf_diff:.0f} above the league average. "
                                    f"Good goal threat from the attacking unit but still {abs(gf_vs_champ):.0f} goals/season short of champion-level output."
                                )
                        elif avg_gf < league_avg_gf_val * 0.90:
                            goals_short = league_avg_gf_val - avg_gf
                            weaknesses.append(
                                f"**Weak goal output** — scoring only {gf_per_game:.2f} goals/game ({avg_gf:.1f}/season), "
                                f"**{goals_short:.0f} fewer than the league average**. "
                                f"This points to a lack of quality in the final third — whether that's finishing (strikers not converting chances), "
                                f"creativity (midfielders not creating enough clear-cut opportunities), or width (full-backs/wingers not delivering "
                                f"enough crosses and cutbacks). Champions average {champ_gf_pg:.2f} goals/game."
                            )
                        elif avg_gf < league_avg_gf_val:
                            weaknesses.append(
                                f"**Slightly below-average attack** — scoring {gf_per_game:.2f} goals/game ({avg_gf:.1f}/season) "
                                f"vs league avg {league_gf_pg:.2f}/game. Not a crisis but an area where marginal improvements "
                                f"(e.g. a more clinical striker, better set-piece delivery) would directly translate to more wins."
                            )

                        if avg_ga < league_avg_ga_val * 0.85:
                            if avg_ga <= champ_avg_ga * 1.05:
                                strengths.append(
                                    f"**Elite defense** — conceding just {ga_per_game:.2f} goals/game ({avg_ga:.1f}/season), "
                                    f"matching championship-winning levels ({champ_ga_pg:.2f}/game). "
                                    f"The centre-back partnership and goalkeeper are providing a rock-solid foundation."
                                )
                            else:
                                strengths.append(
                                    f"**Strong defense** — conceding only {ga_per_game:.2f} goals/game ({avg_ga:.1f}/season), "
                                    f"well below the league average ({league_ga_pg:.2f}/game). "
                                    f"Good defensive structure and organisation across the back line."
                                )
                        elif avg_ga > league_avg_ga_val * 1.10:
                            extra_conceded = avg_ga - league_avg_ga_val
                            weaknesses.append(
                                f"**Leaky defense** — conceding {ga_per_game:.2f} goals/game ({avg_ga:.1f}/season), "
                                f"**{extra_conceded:.0f} more than the league average** per season. "
                                f"This suggests vulnerabilities in central defense (centre-backs being beaten too easily, "
                                f"poor aerial duels, or slow recovery runs), defensive midfield screening (opponents playing through "
                                f"the middle too often), or goalkeeper reliability. Champions concede just {champ_ga_pg:.2f}/game."
                            )
                        elif avg_ga > league_avg_ga_val:
                            weaknesses.append(
                                f"**Slightly porous defense** — conceding {ga_per_game:.2f} goals/game ({avg_ga:.1f}/season) "
                                f"vs league avg {league_ga_pg:.2f}/game. Small improvements in defensive positioning or "
                                f"investing in a better centre-back or defensive midfielder could tighten this up."
                            )

                        if avg_gd > 0 and avg_gf > league_avg_gf_val and avg_ga < league_avg_ga_val:
                            strengths.append(
                                f"**Balanced squad** — positive goal difference of +{avg_gd:.1f}/season with both above-average "
                                f"attacking and defensive records. This balance is the hallmark of a well-coached, well-recruited team."
                            )

                    if has_wdl:
                        win_pct = (avg_w / games_per_season * 100) if games_per_season > 0 else 0
                        champ_win_pct = (champ_avg_w / games_per_season * 100) if games_per_season > 0 else 0
                        draw_pct = (avg_d / games_per_season * 100) if games_per_season > 0 else 0
                        loss_pct = (avg_l / games_per_season * 100) if games_per_season > 0 else 0

                        if avg_w > league_avg_w * 1.2:
                            strengths.append(
                                f"**High win rate ({win_pct:.0f}%)** — averaging {avg_w:.1f} wins/season vs league avg {league_avg_w:.1f}. "
                                f"{'This is near champion level (' + f'{champ_win_pct:.0f}' + '%).' if avg_w >= champ_avg_w * 0.9 else 'Strong mentality in games where they are expected to win.'}"
                            )
                        elif avg_w < league_avg_w * 0.85:
                            wins_short = league_avg_w - avg_w
                            weaknesses.append(
                                f"**Low win rate ({win_pct:.0f}%)** — averaging only {avg_w:.1f} wins/season, "
                                f"**{wins_short:.1f} fewer than average**. This could stem from inability to break down "
                                f"defensive teams (lack of creative midfielders or pacy wingers to unlock tight defences), "
                                f"poor game management (conceding late equalisers), or lack of squad depth to maintain intensity."
                            )

                        if avg_d > league_avg_d * 1.25:
                            extra_draws = avg_d - league_avg_d
                            pts_left = extra_draws * 2
                            weaknesses.append(
                                f"**Draw-prone ({draw_pct:.0f}% of games)** — averaging {avg_d:.1f} draws/season, "
                                f"**{extra_draws:.1f} more than average**, leaving ~{pts_left:.0f} points on the table each season. "
                                f"This typically indicates a team that dominates possession or territory but lacks a cutting edge — "
                                f"either the final ball isn't good enough, the strikers aren't clinical, or the team sits back "
                                f"too early after taking the lead. A more aggressive tactical approach or a "
                                f"game-changing attacker off the bench would help convert draws into wins."
                            )

                        if avg_l < league_avg_l * 0.7:
                            strengths.append(
                                f"**Hard to beat** — losing only {avg_l:.1f} games/season ({loss_pct:.0f}%) vs league avg {league_avg_l:.1f}. "
                                f"This defensive resilience and competitive mentality is a major asset."
                            )
                        elif avg_l > league_avg_l * 1.25:
                            extra_losses = avg_l - league_avg_l
                            weaknesses.append(
                                f"**Lose too often** — averaging {avg_l:.1f} losses/season ({loss_pct:.0f}%), "
                                f"**{extra_losses:.1f} more than average**. Frequent defeats suggest either a quality gap "
                                f"against stronger opponents (need better recruitment), tactical inflexibility (same approach "
                                f"regardless of opponent), or mental fragility (collapsing after conceding first)."
                            )

                    if has_goals and has_wdl:
                        if avg_gd > 0 and avg_pos > top_threshold:
                            weaknesses.append(
                                f"**Inconsistency problem** — positive goal difference (+{avg_gd:.1f}) but average finish "
                                f"of {avg_pos:.1f} (outside top {top_threshold}). This mismatch suggests the team wins big "
                                f"against weaker sides but drops too many points against direct rivals. Better tactical "
                                f"preparation for 'six-pointer' matches and tighter game management when leading are needed."
                            )

                    if len(bench_data) >= 3:
                        recent_3 = bench_data.tail(3)
                        older = bench_data.iloc[:-3] if len(bench_data) > 3 else bench_data
                        if not older.empty:
                            recent_pts = recent_3["Pts"].mean()
                            older_pts = older["Pts"].mean()
                            pts_trend = recent_pts - older_pts
                            if pts_trend > 5:
                                strengths.append(
                                    f"**Improving trajectory** — averaging {recent_pts:.0f} pts in the last 3 completed seasons vs {older_pts:.0f} earlier. "
                                    f"The current project is heading in the right direction with +{pts_trend:.0f} pts improvement."
                                )
                            elif pts_trend < -5:
                                weaknesses.append(
                                    f"**Declining trajectory** — averaging {recent_pts:.0f} pts in the last 3 completed seasons vs {older_pts:.0f} earlier. "
                                    f"A drop of {abs(pts_trend):.0f} pts suggests stagnation or regression — could be ageing squad, "
                                    f"manager bounce wearing off, or failure to reinvest. A squad refresh or tactical rethink may be needed."
                                )

                    if strengths:
                        st.markdown("**Strengths:**")
                        for s in strengths:
                            st.markdown(f"- {s}")

                    if weaknesses:
                        st.markdown("**Areas for Improvement:**")
                        for w in weaknesses:
                            st.markdown(f"- {w}")

                    if not strengths and not weaknesses:
                        st.info("Performance is close to league averages across all metrics — a solid mid-table team with no extreme strengths or weaknesses.")

                    st.divider()
                    st.markdown("### Recommendations")
                    st.markdown(
                        f"Actionable steps for **{selected_team}** to improve their league standing, "
                        f"based on where the data shows the biggest gaps compared to title-winning and top-{top_threshold} teams."
                    )

                    if not hist_champ_pts.empty and not bench_data.empty:
                        bench_latest = bench_data.iloc[-1]
                        latest_pts = bench_latest["Pts"]
                        title_target = hist_champ_pts.mean()
                        top_target = hist_top_pts.quantile(0.5) if not hist_top_pts.empty else title_target
                        pts_gap_title = title_target - latest_pts
                        pts_gap_top = top_target - latest_pts

                        recs = []

                        if pts_gap_title > 0 and games_per_season > 0:
                            extra_wins_needed = pts_gap_title / 3
                            if extra_wins_needed >= 5:
                                recs.append(
                                    f"**Long-term project needed.** The gap to the title ({pts_gap_title:.0f} pts, ~{extra_wins_needed:.0f} extra wins/season) "
                                    f"is significant. Focus on building a squad over 2–3 transfer windows rather than short-term fixes. "
                                    f"Prioritise: a) recruiting young, high-ceiling talent who can grow into the system, "
                                    f"b) developing a clear tactical identity, and c) improving the academy pipeline to reduce reliance on expensive signings."
                                )
                            elif extra_wins_needed >= 2:
                                recs.append(
                                    f"**Within striking distance of the title.** The gap is {pts_gap_title:.0f} pts (~{extra_wins_needed:.1f} more wins/season). "
                                    f"This is closeable with targeted recruitment — a single impact signing in the weakest area of the squad "
                                    f"(see weaknesses above) could be the difference. Also consider tactical tweaks: "
                                    f"being more aggressive at home, better set-piece routines, or a plan B for breaking down deep defences."
                                )
                            else:
                                recs.append(
                                    f"**Title contender.** Just {pts_gap_title:.0f} pts from the historical title average. "
                                    f"At this level, marginal gains matter most — sports science, squad rotation to avoid injuries, "
                                    f"and mental resilience in pressure moments. Keeping key players fit and motivated is more important than new signings."
                                )
                        elif pts_gap_title <= 0:
                            recs.append(
                                f"**Maintaining the standard.** {selected_team}'s latest completed season ({latest_pts:.0f} pts) matches or exceeds "
                                f"the historical title target ({title_target:.0f}). The priority is squad depth and renewal — "
                                f"replacing ageing starters before they decline, keeping wage structure sustainable, and avoiding complacency."
                            )

                        if has_goals and avg_ga > league_avg_ga_val:
                            extra_goals = avg_ga - league_avg_ga_val
                            goals_to_elite = avg_ga - champ_avg_ga
                            pts_from_defense = (extra_goals / games_per_season) * games_per_season * 0.35 * 3 if games_per_season > 0 else 0
                            recs.append(
                                f"**Strengthen the defence.** {selected_team} concedes {extra_goals:.0f} more goals/season than average "
                                f"and {goals_to_elite:.0f} more than champions. Reducing goals conceded could add ~{pts_from_defense:.0f} pts/season. "
                                f"**How:** Invest in a commanding centre-back who wins aerial duels and organises the back line, "
                                f"or a defensive midfielder who shields the defence and cuts passing lanes. "
                                f"If the goalkeeper's save percentage is below par, upgrading there gives immediate improvement. "
                                f"Tactically, work on pressing triggers so the team wins the ball higher up the pitch."
                            )

                        if has_goals and avg_gf < league_avg_gf_val:
                            goals_short = league_avg_gf_val - avg_gf
                            goals_to_elite = champ_avg_gf - avg_gf
                            recs.append(
                                f"**Boost attacking output.** {selected_team} scores {goals_short:.0f} fewer goals/season than average "
                                f"and {goals_to_elite:.0f} fewer than champions. "
                                f"**How:** If the issue is chance creation, recruit a creative midfielder (playmaker) or overlapping "
                                f"full-backs who provide width and crossing. If the issue is finishing, target a proven goalscorer — "
                                f"even a 10-goal-a-season striker would close much of this gap. Better set-piece delivery (corners, "
                                f"free kicks) is one of the most cost-effective ways to add 3–5 goals/season."
                            )

                        if has_wdl and avg_d > league_avg_d * 1.15:
                            extra_draws = avg_d - league_avg_d
                            pts_from_draws = extra_draws * 2
                            half_draws = extra_draws * 0.5
                            recs.append(
                                f"**Convert draws into wins.** {selected_team} draws {extra_draws:.1f} more games/season than average, "
                                f"leaving ~{pts_from_draws:.0f} points on the table. Converting just half of those ({half_draws:.0f} games) "
                                f"would add ~{half_draws * 2:.0f} pts. "
                                f"**How:** Bring on an impact substitute (a pacy forward or attacking midfielder) in drawn games after 60–65 minutes. "
                                f"Train for faster transitions to exploit tired defences. Work on attacking dead-ball situations — "
                                f"late set-piece goals win more tight games than any other approach."
                            )

                        if has_wdl and avg_l > league_avg_l * 1.15:
                            extra_losses = avg_l - league_avg_l
                            recs.append(
                                f"**Reduce heavy defeats.** {selected_team} loses {extra_losses:.1f} more games/season than average. "
                                f"**How:** Adopt a more pragmatic approach against the top sides — sit deeper, stay compact, "
                                f"and play on the counter rather than going toe-to-toe. Improve fitness and concentration levels "
                                f"in the final 15 minutes, where many avoidable goals are conceded. A strong defensive leader "
                                f"(vocal centre-back or experienced goalkeeper) helps prevent collapses."
                            )

                        if has_goals and has_wdl and avg_gf > league_avg_gf_val * 1.1 and avg_ga > league_avg_ga_val * 1.1:
                            recs.append(
                                f"**Fix the imbalance.** {selected_team} scores well but concedes too much — a 'win big, lose big' profile. "
                                f"This team doesn't need more attackers; it needs defensive stability. Consider switching from an expansive "
                                f"formation (e.g. 4-3-3 with high full-backs) to a more balanced shape (e.g. 4-2-3-1 with a double pivot) "
                                f"that provides cover without sacrificing too much going forward. A ball-playing centre-back "
                                f"would let the team build from the back safely."
                            )

                        if len(bench_data) >= 3:
                            recent_3_pts = bench_data.tail(3)["Pts"].mean()
                            if recent_3_pts < avg_pts - 5:
                                recs.append(
                                    f"**Arrest the decline.** Recent form ({recent_3_pts:.0f} pts avg over last 3 seasons) is below "
                                    f"the historical average ({avg_pts:.0f} pts). This may signal a need for a coaching change, "
                                    f"a squad overhaul, or a rethink of the club's recruitment strategy. "
                                    f"Identifying whether the issue is tactical, motivational, or related to player quality "
                                    f"is the first step before spending in the transfer market."
                                )

                        if not recs:
                            recs.append(
                                f"**{selected_team} is performing at or above league benchmarks** across all key metrics. "
                                f"The focus should be on maintaining squad depth, managing player contracts to avoid losing "
                                f"key assets for free, and incremental improvements through smart recruitment and coaching development."
                            )

                        for i, rec in enumerate(recs, 1):
                            st.markdown(f"{i}. {rec}")

                    st.divider()
                    st.markdown("### Season-by-Season Record")
                    display_team = team_data[["Season", "Pos", "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts"]].copy()
                    display_team = display_team[[c for c in display_team.columns if c in team_data.columns]]
                    display_team.index = range(1, len(display_team) + 1)
                    st.dataframe(display_team, use_container_width=True)
                    share_table_buttons(display_team, f"{selected_team} Season Records", f"team_{selected_team}")

                    st.caption(f"Data source: Wikipedia {selected_league} season articles. Points standardised to 3-for-a-win system.")
            else:
                st.warning("Multi-season data is not available. Adjust the season range in the sidebar.")

        with tab7:
            st.header("Cross-League Comparison")
            st.markdown(
                "How does each league compare? This section fetches the current season standings for all "
                "available leagues and compares them on key metrics like scoring rate, defensive strength, "
                "competitiveness, and playing style."
            )

            with st.spinner("Loading cross-league data (this may take a moment on first load)..."):
                cross_df = load_cross_league_comparison()

            if not cross_df.empty:
                failed = cross_df.attrs.get("failed_leagues", [])
                total = cross_df.attrs.get("total_leagues", 0)
                loaded = len(cross_df)
                if failed:
                    st.info(f"Loaded {loaded} of {total} leagues. Could not fetch data for: {', '.join(failed)}.")

                st.subheader("League Overview")
                display_cols = ["League", "Teams", "Goals/Match", "Avg GA", "Best Defence",
                                "Worst Defence", "Draw %", "Pts Spread", "Competitiveness", "Season Progress %"]
                display_cross = cross_df[[c for c in display_cols if c in cross_df.columns]].copy()
                display_cross.index = range(1, len(display_cross) + 1)
                st.dataframe(display_cross, use_container_width=True)
                share_table_buttons(display_cross, "Cross-League Comparison", "cross_league")

                st.markdown("""
**How to read this table:**
- **Goals/Match** — Average goals scored per match. Higher = more attacking league.
- **Avg GA** — Average goals conceded per team. Lower = better overall defending.
- **Best/Worst Defence** — The tightest and leakiest defence in each league (goals conceded).
- **Draw %** — Percentage of matches ending in draws. Higher = more cautious play.
- **Pts Spread** — Gap between 1st and last place. Larger = more dominant top teams.
- **Competitiveness** — Standard deviation of points. Lower = more evenly matched league.
""")

                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    st.subheader("Highest Scoring Leagues")
                    sorted_goals = cross_df.sort_values("Goals/Match", ascending=False)
                    fig_goals = px.bar(
                        sorted_goals, x="League", y="Goals/Match",
                        template="plotly_dark",
                        color="Goals/Match",
                        color_continuous_scale="YlOrRd",
                    )
                    fig_goals.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_goals, use_container_width=True)

                with col_c2:
                    st.subheader("Most Competitive Leagues")
                    sorted_comp = cross_df.sort_values("Competitiveness", ascending=True)
                    fig_comp = px.bar(
                        sorted_comp, x="League", y="Competitiveness",
                        template="plotly_dark",
                        color="Competitiveness",
                        color_continuous_scale="Blues_r",
                    )
                    fig_comp.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_comp, use_container_width=True)

                col_c3, col_c4 = st.columns(2)

                with col_c3:
                    st.subheader("Defensive Strength (Avg Goals Conceded)")
                    sorted_def = cross_df.sort_values("Avg GA", ascending=True)
                    fig_def = px.bar(
                        sorted_def, x="League", y="Avg GA",
                        template="plotly_dark",
                        color="Avg GA",
                        color_continuous_scale="Greens_r",
                    )
                    fig_def.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_def, use_container_width=True)

                with col_c4:
                    st.subheader("Draw Percentage by League")
                    sorted_draw = cross_df.sort_values("Draw %", ascending=False)
                    fig_draw = px.bar(
                        sorted_draw, x="League", y="Draw %",
                        template="plotly_dark",
                        color="Draw %",
                        color_continuous_scale="Purples",
                    )
                    fig_draw.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_draw, use_container_width=True)

                st.subheader("League Comparison Scatter")
                st.markdown("Explore how leagues differ on two dimensions at once.")
                scatter_metrics = ["Goals/Match", "Avg GA", "Draw %", "Pts Spread", "Competitiveness", "Teams"]
                avail_metrics = [m for m in scatter_metrics if m in cross_df.columns]
                if len(avail_metrics) >= 2:
                    sc_col1, sc_col2 = st.columns(2)
                    with sc_col1:
                        x_metric = st.selectbox("X-axis", avail_metrics, index=0, key="cross_scatter_x")
                    with sc_col2:
                        y_default = min(1, len(avail_metrics) - 1)
                        y_metric = st.selectbox("Y-axis", avail_metrics, index=y_default, key="cross_scatter_y")

                    fig_scatter = px.scatter(
                        cross_df, x=x_metric, y=y_metric, text="League",
                        template="plotly_dark", size_max=15,
                        color="Category",
                    )
                    fig_scatter.update_traces(textposition="top center", marker=dict(size=12))
                    fig_scatter.update_layout(height=500)
                    st.plotly_chart(fig_scatter, use_container_width=True)

                st.subheader("Key Takeaways")
                if len(cross_df) >= 2:
                    highest_scoring = cross_df.loc[cross_df["Goals/Match"].idxmax()]
                    lowest_scoring = cross_df.loc[cross_df["Goals/Match"].idxmin()]
                    most_competitive = cross_df.loc[cross_df["Competitiveness"].idxmin()]
                    least_competitive = cross_df.loc[cross_df["Competitiveness"].idxmax()]
                    most_draws = cross_df.loc[cross_df["Draw %"].idxmax()]
                    best_def_league = cross_df.loc[cross_df["Best Defence GA"].idxmin()]

                    takeaways = [
                        f"**Most entertaining league:** {highest_scoring['League']} with **{highest_scoring['Goals/Match']} goals per match** — "
                        f"expect end-to-end action.",
                        f"**Most defensive league:** {lowest_scoring['League']} averaging **{lowest_scoring['Goals/Match']} goals per match** — "
                        f"tight, tactical affairs.",
                        f"**Most competitive league:** {most_competitive['League']} (pts std dev: {most_competitive['Competitiveness']}) — "
                        f"any team can beat any team on their day.",
                        f"**Most one-sided league:** {least_competitive['League']} (pts std dev: {least_competitive['Competitiveness']}) — "
                        f"a bigger gap between top and bottom.",
                        f"**Most cautious league:** {most_draws['League']} with **{most_draws['Draw %']}% draws** — "
                        f"teams prefer not to lose over trying to win.",
                        f"**Best single defence across all leagues:** {best_def_league['Best Defence']} "
                        f"in the {best_def_league['League']}.",
                    ]
                    for t in takeaways:
                        st.markdown(f"- {t}")

                st.caption("Data source: Wikipedia current-season league articles. Metrics are based on the season in progress and will update as more matches are played.")
            else:
                st.warning("Could not load cross-league comparison data. Please try again later.")

except requests.exceptions.HTTPError as e:
    _status = e.response.status_code if e.response is not None else "unknown"
    if _status == 404:
        if season is not None:
            season_label = format_season_label(season, league_cfg["season_type"])
            st.warning(
                f"The Wikipedia page for the {selected_league} {season_label} season could not be found. "
                f"Try selecting a different season, or this season may not yet have a Wikipedia article."
            )
        else:
            st.warning(f"Could not find data for the {selected_league}. Try another competition.")
    elif _status in (429, 503):
        st.warning("The data source is temporarily unavailable (rate limited or overloaded). Please try again in a moment.")
    else:
        st.warning(f"Could not fetch data (HTTP {_status}). The page may have moved or be temporarily unavailable.")
except Exception as e:
    st.warning(f"Something went wrong loading this league's data. Please try refreshing or selecting a different season. (Detail: {e})")

st.divider()
st.markdown(
    '<div style="text-align:center;padding:8px 0;color:#888;font-size:0.85em;">'
    'Data Source: <a href="https://fbref.com" target="_blank" style="color:#888;">FBref</a> '
    '| <a href="https://en.wikipedia.org" target="_blank" style="color:#888;">Wikipedia</a> '
    '| <a href="https://www.transfermarkt.com" target="_blank" style="color:#888;">Transfermarkt</a>'
    '</div>',
    unsafe_allow_html=True,
)

st.divider()
st.markdown("**Want to leave feedback?** Use the **Feedback** tab in the sidebar navigation to rate this dashboard and see what others think.")
