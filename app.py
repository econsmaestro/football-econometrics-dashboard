import streamlit as st
import pandas as pd
import numpy as np
import requests
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


try:
    with st.spinner("Fetching league data..."):
        single_season = fetch_season_data(int(season))
        multi_season = load_multi_season(season_range[0], season_range[1])

    tab1, tab2, tab3, tab4 = st.tabs([
        "League Table",
        "Statistical Analysis",
        "Visualizations",
        "Predictions & Insights",
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
        st.markdown("Based on the OLS regression model (Pts ~ GF + GA), estimate expected points for a hypothetical team:")

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

            col_pred1, col_pred2, col_pred3 = st.columns(3)
            col_pred1.metric("Predicted Points", f"{predicted_pts:.1f}")
            col_pred2.metric("95% CI Lower", f"{pi[0]:.1f}")
            col_pred3.metric("95% CI Upper", f"{pi[1]:.1f}")

            recent = multi_season[multi_season["Season_End"] == multi_season["Season_End"].max()]
            if not recent.empty:
                closest = recent.iloc[(recent["Pts"] - predicted_pts).abs().argsort()[:1]]
                st.markdown(
                    f"A team with {pred_gf} goals scored and {pred_ga} conceded would be expected to "
                    f"finish with approximately **{predicted_pts:.0f} points**, similar to "
                    f"**{closest['Squad'].values[0]}** ({closest['Pts'].values[0]:.0f} pts) "
                    f"in the most recent season."
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

except requests.exceptions.HTTPError:
    st.error(f"Could not fetch data for the {season - 1}-{season} season. The page may not be available.")
except Exception as e:
    st.error(f"An error occurred: {e}")
