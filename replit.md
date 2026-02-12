# Football Econometrics Dashboard

## Overview

A reproducible football analytics/econometrics study built with Streamlit that shows what statistically matters for success in the English Premier League. The app covers all Premier League seasons from 1992-93 through the current season (auto-detected), offering league tables, statistical analysis (OLS regression, correlation matrices), interactive visualizations, a points predictor, and a penalty analysis system with goalkeeper positioning advice.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **2026-02-12**: Added Penalty Analysis tab (tab 5) with Transfermarkt scraping for penalty taker/goalkeeper stats, shot placement zone visualization, Bayesian prediction model, and goalkeeper diving advice.
- **2026-02-12**: Expanded from simple league table to full econometrics dashboard with 4 tabs (League Table, Statistical Analysis, Visualizations, Predictions & Insights). Added multi-season data loading, OLS regression models, correlation analysis, scatter/box/bar plots, and a points predictor with confidence intervals.
- **2026-02-12**: Switched data source from FBRef (blocked with 403) to Wikipedia Premier League season articles.

## System Architecture

### Frontend
- **Framework**: Streamlit with wide layout
- **Entry point**: `app.py` — run with `streamlit run app.py --server.port 5000`
- **Tabs**: League Table, Statistical Analysis, Visualizations, Predictions & Insights, Penalty Analysis
- **Sidebar**: Season selector (1992-current), season range slider for multi-season analysis

### Data Layer
- **League data source**: Wikipedia Premier League season articles (e.g., `https://en.wikipedia.org/wiki/2023–24_Premier_League`)
- **Penalty data source**: Transfermarkt penalty taker + goalkeeper save pages
- **Scraping**: `requests` + `pandas.read_html()` for Wikipedia; `requests` + `BeautifulSoup` for Transfermarkt
- **Caching**: `@st.cache_data` with 1-hour TTL
- **Variables extracted**: Pos, Squad, Pld, W, D, L, GF, GA, GD, Pts
- **Derived metrics**: PPG (points per game), Win%, GF/Game, GA/Game

### Analytics
- **Correlation matrix**: Heatmap of all numeric variables
- **OLS Regression**: Two models — Pts ~ GF + GA, and Pts ~ W + D + L (via statsmodels)
- **Visualizations**: Plotly scatter plots with trendlines, bar charts, box plots, line charts
- **Predictor**: Regression-based points prediction with 95% confidence intervals
- **Penalty predictor**: Bayesian shrinkage model combining taker conversion + GK save rate + league averages
- **Shot placement zones**: 8-zone goal visualization with taker % and GK save % per zone (from research data)

### File Structure
- `app.py` — Main Streamlit application (scraping, analysis, UI)
- `main.py` — Placeholder (not used)
- `.streamlit/config.toml` — Streamlit server config (port 5000, headless)

## External Dependencies

### Python Packages
- **streamlit** — Web dashboard framework
- **pandas** — Data manipulation and HTML table parsing
- **requests** — HTTP requests for web scraping
- **plotly** — Interactive visualizations
- **statsmodels** — OLS regression and statistical modeling
- **scipy** — Statistical tests (Pearson correlation)
- **scikit-learn** — ML utilities (available but not directly used yet)
- **beautifulsoup4**, **lxml**, **html5lib** — HTML parsing support

### External Services
- **Wikipedia** — Primary data source for Premier League standings by season
- **Transfermarkt** — Penalty taker and goalkeeper save statistics

### No Database
- All data is fetched on-demand and cached in memory.
