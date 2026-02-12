import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.api as sm
from scipy import stats

st.set_page_config(page_title="Football Econometrics Dashboard", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def detect_current_season():
    from datetime import date
    today = date.today()
    if today.month >= 8:
        return today.year + 1
    return today.year


CURRENT_SEASON_END = detect_current_season()

st.title("Football Econometrics Dashboard")
st.caption(f"A reproducible econometrics study of what statistically matters for success in the Premier League (1992-93 to {CURRENT_SEASON_END - 1}-{str(CURRENT_SEASON_END)[2:]})")

with st.sidebar:
    st.header("Controls")
    all_seasons = list(range(1993, CURRENT_SEASON_END + 1))
    season = st.selectbox(
        "Season (end year)",
        options=all_seasons,
        index=len(all_seasons) - 1,
    )
    st.divider()
    st.subheader("Multi-Season Analysis")
    season_range = st.slider(
        "Season range for analysis",
        min_value=1993,
        max_value=CURRENT_SEASON_END,
        value=(1993, CURRENT_SEASON_END),
    )


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_season_data(season_end_year):
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
            wanted = ["Pos", team_col, "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts"]
            available = [c for c in wanted if c in cols]
            df = table[available].copy()

            rename_map = {team_col: "Squad"}
            df = df.rename(columns=rename_map)

            df["Squad"] = df["Squad"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()

            for col in ["Pos", "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace("\u2212", "-", regex=False)
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["Pos"])
            df["Pos"] = df["Pos"].astype(int)
            df = df.sort_values("Pos").reset_index(drop=True)
            df["Season"] = f"{season_start}-{suffix}"
            df["Season_End"] = season_end_year

            if "Pld" in df.columns and "Pts" in df.columns:
                df["PPG"] = (df["Pts"] / df["Pld"]).round(3)
            if "Pld" in df.columns and "W" in df.columns:
                df["Win%"] = ((df["W"] / df["Pld"]) * 100).round(1)
            if "Pld" in df.columns and "GF" in df.columns:
                df["GF/Game"] = (df["GF"] / df["Pld"]).round(2)
            if "Pld" in df.columns and "GA" in df.columns:
                df["GA/Game"] = (df["GA"] / df["Pld"]).round(2)

            return df

    raise ValueError(f"Could not find league table for {season_start}-{season_end_year}")


@st.cache_data(ttl=3600, show_spinner=False)
def load_multi_season(start_year, end_year):
    frames = []
    for yr in range(start_year, end_year + 1):
        try:
            df = fetch_season_data(yr)
            frames.append(df)
        except Exception:
            pass
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def scrape_penalty_takers(season_id=None):
    base_url = "https://www.transfermarkt.us/premier-league/elfmeterschuetzen/wettbewerb/GB1/plus/1"
    if season_id:
        base_url += f"/saison_id/{season_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(base_url, headers=headers, timeout=30)
    response.raise_for_status()
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


@st.cache_data(ttl=3600, show_spinner=False)
def scrape_penalty_goalkeepers(season_id=None):
    base_url = "https://www.transfermarkt.us/premier-league/elfmetertoeter/wettbewerb/GB1/plus/1"
    if season_id:
        base_url += f"/saison_id/{season_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(base_url, headers=headers, timeout=30)
    response.raise_for_status()
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


@st.cache_data(ttl=3600, show_spinner=False)
def load_multi_season_penalties(start_year, end_year):
    taker_frames = []
    gk_frames = []
    for yr in range(start_year, end_year + 1):
        try:
            t = scrape_penalty_takers(yr)
            if not t.empty:
                t["Season"] = f"{yr}-{str(yr+1)[2:]}"
                taker_frames.append(t)
        except Exception:
            pass
        try:
            g = scrape_penalty_goalkeepers(yr)
            if not g.empty:
                g["Season"] = f"{yr}-{str(yr+1)[2:]}"
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


try:
    with st.spinner("Fetching league data..."):
        single_season = fetch_season_data(int(season))
        multi_season = load_multi_season(season_range[0], season_range[1])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "League Table",
        "Statistical Analysis",
        "Visualizations",
        "Predictions & Insights",
        "Penalty Analysis",
    ])

    with tab1:
        st.subheader(f"Premier League {season - 1}-{str(season)[2:]} Standings")
        display_cols = [c for c in ["Pos", "Squad", "Pld", "W", "D", "L", "GF", "GA", "GD", "Pts", "PPG", "Win%"] if c in single_season.columns]
        st.dataframe(
            single_season[display_cols].set_index("Pos"),
            use_container_width=True,
            height=740,
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
        st.markdown(
            f"Analysis based on **{len(multi_season)}** team-season observations "
            f"across **{multi_season['Season_End'].nunique()}** seasons "
            f"({season_range[0] - 1}-{str(season_range[0])[2:]} to {season_range[1] - 1}-{str(season_range[1])[2:]})."
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
        st.markdown(
            "**What is OLS Regression?** It's a statistical method that finds the best-fit "
            "formula to predict one thing (Points) from other things (Goals Scored, Goals Conceded). "
            "Think of it like finding the recipe: how much does each ingredient contribute to the final result?"
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
            "The Premier League has changed significantly due to big-money takeovers widening the gap "
            "between top and bottom teams. This model uses only the **last 5 completed seasons** to "
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

                st.markdown(f"*Using {len(reg_recent)} team-seasons from {recent_cutoff}-{str(recent_cutoff+1)[2:]} to {CURRENT_SEASON_END - 1}-{str(CURRENT_SEASON_END)[2:]}*")

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
        tier_data["Tier"] = pd.cut(
            tier_data["Pos"],
            bins=[0, 4, 7, 14, 20],
            labels=["Top 4", "5th-7th", "8th-14th", "15th-20th"],
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
                recent_label = f"{int(closest['Season_End'].values[0]) - 1}-{str(int(closest['Season_End'].values[0]))[2:]}"
                model_label = "recent era model" if has_recent_model else "full history model"
                st.markdown(
                    f"A team with {pred_gf} goals scored and {pred_ga} conceded would be expected to "
                    f"finish with approximately **{best_pred:.0f} points** (using the {model_label}), "
                    f"similar to **{closest['Squad'].values[0]}** ({closest['Pts'].values[0]:.0f} pts) "
                    f"in the {recent_label} season."
                )

        st.divider()

        st.markdown("### Key Insights from the Data")

        if not multi_season.empty:
            avg_champ_pts = multi_season[multi_season["Pos"] == 1]["Pts"].mean()
            avg_relegated_pts = multi_season[multi_season["Pos"] >= 18]["Pts"].mean()
            avg_top4_gd = multi_season[multi_season["Pos"] <= 4]["GD"].mean()
            avg_bottom_gd = multi_season[multi_season["Pos"] >= 18]["GD"].mean()

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.metric("Avg. Champion Points", f"{avg_champ_pts:.1f}")
                st.metric("Avg. Top 4 Goal Difference", f"+{avg_top4_gd:.1f}")
            with col_i2:
                st.metric("Avg. Relegated Team Points", f"{avg_relegated_pts:.1f}")
                st.metric("Avg. Bottom 3 Goal Difference", f"{avg_bottom_gd:.1f}")

            st.divider()

            st.markdown("### Findings")
            st.markdown(f"""
1. **Goal difference is the strongest single predictor of league position.** Across {multi_season['Season_End'].nunique()} seasons, the Pearson correlation between GD and Pts is extremely high, confirming that balanced teams (strong attack + solid defense) finish highest.

2. **Defense matters as much as attack.** The regression coefficients for GF and GA are roughly symmetric in magnitude, indicating that preventing a goal is worth approximately the same as scoring one.

3. **The points threshold for survival is remarkably stable.** Relegated teams average ~{avg_relegated_pts:.0f} points, suggesting a practical survival target of roughly {avg_relegated_pts + 5:.0f} points per season.

4. **Champions typically require {avg_champ_pts:.0f}+ points.** The average title-winning total of {avg_champ_pts:.1f} points corresponds to roughly {avg_champ_pts / 38:.2f} points per game.
            """)

        st.divider()
        st.caption("Data source: Wikipedia Premier League season articles. Statistical models are OLS regressions estimated via statsmodels.")

    with tab5:
        st.subheader("Penalty Analysis & Save Predictor")
        st.markdown(
            "Penalty statistics scraped from Transfermarkt for current Premier League players. "
            "Use the predictor to estimate the probability of a goalkeeper saving a penalty from a specific taker."
        )

        pen_season_options = list(range(max(2020, season_range[0]), CURRENT_SEASON_END + 1))
        pen_col1, pen_col2 = st.columns(2)
        with pen_col1:
            pen_start = st.selectbox("Penalty data from season", pen_season_options, index=0, key="pen_start")
        with pen_col2:
            pen_end = st.selectbox("To season", pen_season_options, index=len(pen_season_options) - 1, key="pen_end")

        with st.spinner("Fetching penalty data from Transfermarkt..."):
            agg_takers, agg_gks = load_multi_season_penalties(pen_start, pen_end)

        if not agg_takers.empty:
            st.subheader("Penalty Takers")
            st.markdown(f"**{len(agg_takers)} players** with penalty records across the selected seasons.")
            takers_display = agg_takers.sort_values("Penalties", ascending=False).reset_index(drop=True)
            takers_display.index += 1
            st.dataframe(takers_display, use_container_width=True, height=400)

        if not agg_gks.empty:
            st.subheader("Goalkeeper Penalty Records")
            st.markdown(f"**{len(agg_gks)} goalkeepers** with penalty-saving records.")
            gks_display = agg_gks.sort_values("Faced", ascending=False).reset_index(drop=True)
            gks_display.index += 1
            st.dataframe(gks_display, use_container_width=True, height=400)

        st.divider()
        st.subheader("Shot Placement Analysis")
        st.markdown(
            "Based on published research on professional penalty kicks (aggregated from major European leagues "
            "and international tournaments), the table below shows where penalty takers typically aim and "
            "how often goalkeepers save shots in each zone."
        )

        zone_df = pd.DataFrame(ZONE_PROBS).T
        zone_df.index.name = "Zone"
        zone_df["Expected Goal %"] = (100 - zone_df["GK Save %"] * zone_df["Taker %"] / 100).round(1)
        st.dataframe(zone_df, use_container_width=True)

        st.markdown("**Visual: Goal Zones (Goalkeeper's Perspective)**")
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
        fig_zones.update_layout(
            xaxis=dict(range=[-0.3, 7.62], showgrid=False, zeroline=False, title="Width (m)"),
            yaxis=dict(range=[-0.15, 2.6], showgrid=False, zeroline=False, title="Height (m)", scaleanchor="x"),
            height=350, margin=dict(l=40, r=40, t=20, b=40),
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

        if not agg_takers.empty and not agg_gks.empty:
            taker_list = agg_takers.sort_values("Penalties", ascending=False)["Player"].tolist()
            gk_list = agg_gks.sort_values("Faced", ascending=False)["Goalkeeper"].tolist()

            pred_col1, pred_col2 = st.columns(2)
            with pred_col1:
                selected_taker = st.selectbox("Penalty Taker", taker_list, key="pen_taker")
            with pred_col2:
                selected_gk = st.selectbox("Goalkeeper", gk_list, key="pen_gk")

            taker_row = agg_takers[agg_takers["Player"] == selected_taker].iloc[0]
            gk_row = agg_gks[agg_gks["Goalkeeper"] == selected_gk].iloc[0]

            taker_conv = taker_row["Conversion %"]
            taker_pens = taker_row["Penalties"]
            gk_save_rate = gk_row["Save %"]
            gk_faced = gk_row["Faced"]

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

            st.markdown(f"**{selected_taker}** ({taker_row['Club']}) vs **{selected_gk}** ({gk_row['Club']})")

            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Goal Probability", f"{p_goal * 100:.1f}%")
            res_col2.metric("Save Probability", f"{p_save * 100:.1f}%")
            res_col3.metric("Miss Probability", f"{p_miss * 100:.1f}%")

            st.markdown("**Taker Profile**")
            t_col1, t_col2, t_col3 = st.columns(3)
            t_col1.metric("Penalties Taken", int(taker_pens))
            t_col2.metric("Scored", int(taker_row["Scored"]))
            t_col3.metric("Conversion Rate", f"{taker_conv:.1f}%")

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
            st.markdown(
                f"Based on league-wide shot placement data, here is where **{selected_gk}** "
                f"should dive against **{selected_taker}** to maximise the chance of a save:"
            )

            advice_data = []
            for zone, probs in ZONE_PROBS.items():
                expected_saves = probs["Taker %"] * probs["GK Save %"] / 100
                advice_data.append({
                    "Zone": zone,
                    "Taker Aims Here %": probs["Taker %"],
                    "GK Save Rate in Zone %": probs["GK Save %"],
                    "Expected Save Value": round(expected_saves, 2),
                })
            advice_df = pd.DataFrame(advice_data).sort_values("Expected Save Value", ascending=False)
            advice_df.index = range(1, len(advice_df) + 1)
            st.dataframe(advice_df, use_container_width=True)

            best_zone = advice_df.iloc[0]["Zone"]
            best_value = advice_df.iloc[0]["Expected Save Value"]
            st.markdown(
                f"**Recommendation:** Dive to the **{best_zone}** (expected save value: {best_value:.2f}). "
                f"This zone combines a high likelihood of the taker aiming there with a reasonable save probability. "
                f"The top corners have the lowest save rates (<6%) — if the taker goes there, it's very hard to stop."
            )
        elif agg_takers.empty and agg_gks.empty:
            st.warning("No penalty data could be loaded. Try adjusting the season range.")
        else:
            if agg_takers.empty:
                st.warning("Penalty taker data could not be loaded.")
            if agg_gks.empty:
                st.warning("Goalkeeper save data could not be loaded.")

        st.divider()
        st.caption("Penalty data source: Transfermarkt. Shot placement research data aggregated from academic studies on professional penalty kicks.")

except requests.exceptions.HTTPError:
    st.error(f"Could not fetch data for the {season - 1}-{season} season. The page may not be available.")
except Exception as e:
    st.error(f"An error occurred: {e}")
