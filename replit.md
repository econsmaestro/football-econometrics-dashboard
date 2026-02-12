# Football Econometrics Dashboard

## Overview

A reproducible football analytics/econometrics study built with Streamlit that shows what statistically matters for success across 30 football competitions worldwide (23 leagues + 7 cup/tournament competitions). The app supports split-season (e.g. Premier League, La Liga) and calendar-season (e.g. MLS, J1 League) formats, offering league tables, statistical analysis (OLS regression, correlation matrices), interactive visualizations, a points predictor, and a penalty analysis system with game-theory adjustments and goalkeeper positioning advice.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **2026-02-12**: Added Team Insights tab (tab 6) — select any team for personalised analysis including KPI overview, historical trends (PPG, goals, position), peer benchmarking vs league/top-N/champion, trophy target thresholds, automated strengths/weaknesses detection, data-driven recommendations, and season-by-season records. Dynamic top-N and relegation thresholds based on league size.
- **2026-02-12**: Added Career Penalty Lookup feature — search any player by name to see their entire career penalty record across all top-flight competitions worldwide (not just the selected league). Uses Transfermarkt player search + individual player penalty page scraping with header-based column mapping for robust parsing. Shows competition/club breakdowns, charts, goalkeeper-beaten stats, and full detailed penalty record.
- **2026-02-12**: Added 7 cup/tournament competitions (Europa League, Conference League, FIFA World Cup, UEFA Euros, AFC Asian Cup, Copa América, CONMEBOL Libertadores) with proper Transfermarkt `pokalwettbewerb` URL handling. Reorganized sidebar with category-grouped Competition dropdown. Tournaments show penalty-only tab.
- **2026-02-12**: Expanded to 23 leagues with all-time penalty taker/GK records. Added game-theory adjusted penalty analysis, dynamic tier binning, URL-encoded Wikipedia names for non-ASCII leagues. Champions League shows penalty-only tab; leagues without GK data gracefully disable predictor.
- **2026-02-12**: Added Penalty Analysis tab (tab 5) with Transfermarkt scraping for penalty taker/goalkeeper stats, shot placement zone visualization, Bayesian prediction model, game-theory strategic adjustment, and goalkeeper diving advice (all from GK's perspective).
- **2026-02-12**: Expanded from simple league table to full econometrics dashboard with 5 tabs. Added multi-season data loading, OLS regression models (full history + recent era), correlation analysis, scatter/box/bar plots, points predictor with confidence intervals.
- **2026-02-12**: Switched data source from FBRef (blocked with 403) to Wikipedia season articles.

## System Architecture

### Frontend
- **Framework**: Streamlit with wide layout
- **Entry point**: `app.py` — run with `streamlit run app.py --server.port 5000`
- **Tabs (leagues)**: League Table, Statistical Analysis, Visualizations, Predictions & Insights, Penalty Analysis
- **Tabs (tournaments)**: Penalty Analysis only
- **Sidebar**: Competition selector (30 competitions grouped by category), season selector (adapts per league type), season range slider for multi-season analysis. Tournaments show info message instead of season controls.

### League Configuration
- **LEAGUE_CONFIG**: Dictionary mapping competition names to parameters:
  - `tm_slug`, `tm_code`: Transfermarkt URL components
  - `wiki_pattern`: "split" or "calendar" (or None for cups/tournaments)
  - `wiki_name`: Wikipedia article suffix (URL-encoded for non-ASCII)
  - `start_year`, `teams`, `games_per_season`: Competition-specific parameters
  - `has_gk_data`: Whether Transfermarkt GK penalty data is available
  - `season_type`: "split" (2023-24) or "calendar" (2024)
  - `is_cup`: True for cup/tournament competitions (uses `pokalwettbewerb` URL pattern)
  - `category`: Grouping category for sidebar display

### Supported Competitions
- **Europe (leagues)**: Premier League, La Liga, Ligue 1, Bundesliga, Serie A, Eredivisie, Scottish Premiership
- **UEFA Competitions (cups)**: Champions League, Europa League, Conference League
- **International (cups)**: FIFA World Cup, UEFA European Championship, AFC Asian Cup, Copa América, CONMEBOL Libertadores
- **Middle East**: Saudi Pro League
- **Asia**: Indian Super League, J1 League, K League 1, Singapore Premier League
- **Americas**: MLS, Argentine Primera División, Brasileirão Série A, Liga BetPlay (Colombia), Chilean/Uruguayan/Paraguayan/Peruvian/Bolivian/Venezuelan Primera División

### Data Layer
- **League data source**: Wikipedia season articles (split-season: `{start}–{suffix}_{League}`, calendar-season: `{year}_{League}`)
- **Penalty data source**: Transfermarkt penalty taker + goalkeeper save pages
  - Leagues use `/wettbewerb/{code}` URL pattern
  - Cups use `/pokalwettbewerb/{code}` URL pattern
- **All-time records**: Scraped from each competition's founding year to present
- **Scraping**: `requests` + `pandas.read_html()` for Wikipedia; `requests` + `BeautifulSoup` for Transfermarkt
- **Caching**: `@st.cache_data` with 1-hour TTL, keyed per competition
- **Column detection**: Flexible parsing handles Team/Teamvte/Club/Clubvte/Squad and Pld/MP/P column names

### Analytics
- **Correlation matrix**: Heatmap of all numeric variables
- **OLS Regression**: Three models — Pts ~ GF + GA (full history), Pts ~ GF + GA (recent 5 seasons), Pts ~ W + D + L
- **Visualizations**: Plotly scatter plots with trendlines, bar charts, box plots (dynamic tier bins), line charts
- **Predictor**: Regression-based points prediction with 95% confidence intervals
- **Penalty predictor**: Bayesian shrinkage model combining taker conversion + GK save rate + league averages
- **Game-theory adjustment**: Strategic shift analysis accounting for how takers adapt shot placement based on GK reputation
- **Shot placement zones**: 8-zone goal visualization with taker % and GK save % per zone (from research data)

### File Structure
- `app.py` — Main Streamlit application (config, scraping, analysis, UI)
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
- **Wikipedia** — Primary data source for league standings by season (all supported leagues)
- **Transfermarkt** — Penalty taker and goalkeeper save statistics (leagues and cups)

### No Database
- All data is fetched on-demand and cached in memory.
