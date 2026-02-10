# Football Econometrics Dashboard

## Overview

This is a Football Econometrics Dashboard built with Streamlit that scrapes and displays advanced football (soccer) statistics from FBRef.com. The application allows users to explore player and team statistics across Europe's top 5 leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1) for seasons from 2014-15 through 2023-24.

The project is in early development — the core scraping function exists but is incomplete (no response handling or data parsing yet), and the dashboard UI is minimal.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
- **Framework**: Streamlit, a Python-based web framework for data dashboards
- **Layout**: Uses Streamlit's wide layout mode with a sidebar for user controls (season selection)
- **Entry point**: `app.py` is the main Streamlit application; run with `streamlit run app.py`

### Data Layer
- **Data source**: Web scraping from FBRef.com (fbref.com), which provides detailed football statistics
- **Scraping approach**: Uses `requests` library with custom User-Agent headers to fetch HTML pages, with `pandas` (likely `pd.read_html()`) for parsing HTML tables
- **Caching**: Streamlit's `@st.cache_data` decorator with a 1-hour TTL to avoid repeated scraping requests
- **Supported leagues**: England (Premier League, comp_id=9), Spain (La Liga, comp_id=12), Italy (Serie A, comp_id=11), Germany (Bundesliga, comp_id=20), France (Ligue 1, comp_id=13)

### Key Design Decisions
1. **Streamlit over Flask/Django**: Chosen for rapid prototyping of data dashboards without needing separate frontend code. Good for data-focused applications but limited for complex UI.
2. **Direct web scraping over API**: FBRef doesn't offer a public API, so HTML scraping is used. This is fragile — URL patterns and HTML structure can change.
3. **In-memory caching**: No database is used; data is cached in Streamlit's session/app cache. This keeps the architecture simple but means data is re-fetched when cache expires.

### File Structure
- `app.py` — Main Streamlit application with scraping logic and dashboard UI
- `main.py` — Placeholder/default entry point (not used by the dashboard)

## External Dependencies

### Python Packages
- **streamlit** — Web dashboard framework
- **pandas** — Data manipulation and HTML table parsing
- **requests** — HTTP requests for web scraping

### External Services
- **FBRef.com** — Primary data source for football statistics. URLs follow the pattern: `https://fbref.com/en/comps/{comp_id}/{season_start}-{season_end}/stats/...`
- Note: FBRef has rate limiting; the `time` module is imported (likely for adding delays between requests) and a custom User-Agent header is set to avoid being blocked

### No Database
- The application currently has no database. All data is fetched on-demand and cached in memory.