# Football Econometrics Dashboard

## Overview

A reproducible football analytics/econometrics study built with Streamlit that shows what statistically matters for success across 30 football competitions worldwide (23 leagues + 7 cup/tournament competitions). The app supports split-season (e.g. Premier League, La Liga) and calendar-season (e.g. MLS, J1 League) formats, offering league tables, statistical analysis (OLS regression, correlation matrices), interactive visualizations, a points predictor, and a penalty analysis system with game-theory adjustments and goalkeeper positioning advice.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **2026-03-26**: Added static fallback CSVs (Premier League, La Liga, Bundesliga, Serie A, Ligue 1 — 2023-24 final standings) under `fallback_data/`. When all Wikipedia scraping fails, app loads the relevant CSV and shows a clear `st.error()` banner instead of a blank screen. Error messages are now human-readable: 404 → season page not yet published; 429 → rate-limited; 5xx → server error; connection errors → network issue; parse failure → Wikipedia layout changed. Extracted pure functions (`format_season_label`, `render_star_display`, `rebase_to_standard_season`, `fit_ols_goals_model`, `predict_points`, `bayesian_penalty_conversion`, `load_fallback_data`) into `models.py`. Added `tests/test_core.py` with 32 unit tests (all passing) covering season labelling, star display, rebasing logic, OLS regression, Bayesian penalty model, and fallback data loading. Run with `python -m pytest tests/ -v`.
- **2026-03-10**: Added dedicated Feedback Dashboard page (nav sidebar) with submit form, goal-scoring SVG animation on submission (ball into net with confetti and "GOAL!" text), rating distribution bar chart, sentiment breakdown pie chart, all reviews list with rating filter, and metrics (total reviews, average rating, 5-star count). Moved feedback form from bottom of main dashboard to dedicated page.
- **2026-02-17**: Added League Comparisons tab (tab 7) — cross-league comparison fetching current-season data for all leagues, showing goals per match, defensive strength, competitiveness, draw rates, and auto-generated takeaways. Includes bar charts, interactive scatter plot, and CSV download. Added CSV download buttons on major tables. Added weekly insights section with overperformers, underperformers, title odds, best attack/defence, and relegation watch. Fixed rating distribution chart colors (green/blue/yellow/red by star). Fixed league logo visibility with white circular background and onerror fallback. Fixed crash for leagues without Wikipedia data.
- **2026-02-13**: Added user feedback system with 1-5 star ratings, optional text comments, and username. Good reviews (4-5 stars) are displayed on the Dashboard homepage in styled cards; bad reviews (1-3 stars) are hidden from public view. Added web analytics page showing total unique visitors, total page views, daily traffic chart (30 days), most visited pages, review statistics, and rating distribution. Uses PostgreSQL database for persistent storage.
- **2026-02-12**: Updated league configs with researched accurate values: J1 League (20 teams, 38 games from 2025 expansion), K League 1 (12 teams, 38 games incl. split round), ISL (13 teams, 24 games), MLS (30 teams, 34 games), Argentine (30 teams). Rebasing auto-normalizes historical seasons with different formats.
- **2026-02-12**: Added season rebasing — seasons with different numbers of games (e.g. PL's 42-game era before 1995-96, Serie A's 34-game era before 2004-05, Ligue 1's 38-game era before 2023-24) are automatically scaled to the league's current standard for fair cross-season comparison. Only complete seasons are rebased; in-progress seasons keep actual values. Visual indicators show when rebasing has been applied in League Table, Statistical Analysis, and Team Insights tabs.
- **2026-02-12**: Added incomplete season detection — benchmarking, strengths/weaknesses, and recommendations use only completed seasons (Pld >= games_per_season) to avoid misleading comparisons with in-progress seasons.
- **2026-02-12**: Enhanced Team Insights — added Goal Sources & Top Scorers section with paginated Transfermarkt scraping (all scorers, not just top 25). Shows goals by type (open play vs penalties), goals by position group (donut chart), top scorer bar chart, dependency analysis, penalty reliance warnings, and midfield contribution insights. Enhanced strengths/weaknesses with specific football-tactical advice (mentioning positions like centre-back, defensive midfielder, striker, goalkeeper) and champion-level benchmarking. Recommendations now provide actionable football advice (formations, transfer targets, set-piece improvement, tactical adjustments) instead of generic stats.
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
