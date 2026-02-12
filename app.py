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

st.title("Football Econometrics Dashboard")
st.caption("A reproducible econometrics study of what statistically matters for success in the Premier League (1992-93 to 2024-25)")

with st.sidebar:
    st.header("Controls")
    season = st.selectbox(
        "Season (end year)",
        options=list(range(1993, 2026)),
        index=32,
    )
    st.divider()
    st.subheader("Multi-Season Analysis")
    season_range = st.slider(
        "Season range for analysis",
        min_value=1993,
        max_value=2025,
        value=(1993, 2025),
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

        st.subheader("Correlation Matrix")
        corr_matrix = corr_data.corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            aspect="auto",
        )
        fig_corr.update_layout(height=500)
        st.plotly_chart(fig_corr, use_container_width=True)

        st.subheader("OLS Regression: Points as Dependent Variable")
        st.markdown("Estimating: **Pts = β₀ + β₁·GF + β₂·GA + ε**")

        if "GF" in multi_season.columns and "GA" in multi_season.columns:
            reg_data = multi_season[["Pts", "GF", "GA"]].dropna()
            X = sm.add_constant(reg_data[["GF", "GA"]])
            y = reg_data["Pts"]
            model = sm.OLS(y, X).fit()

            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("R-squared", f"{model.rsquared:.4f}")
            col_r2.metric("Adj. R-squared", f"{model.rsquared_adj:.4f}")
            col_r3.metric("F-statistic", f"{model.fvalue:.2f}")

            st.markdown("**Coefficient Estimates**")
            coef_df = pd.DataFrame({
                "Variable": model.params.index,
                "Coefficient": model.params.values.round(4),
                "Std. Error": model.bse.values.round(4),
                "t-value": model.tvalues.values.round(4),
                "p-value": model.pvalues.values.round(6),
            })
            st.dataframe(coef_df.set_index("Variable"), use_container_width=True)

            st.markdown(
                f"**Interpretation:** Each additional goal scored is associated with "
                f"**{model.params['GF']:.3f}** more points, while each additional goal "
                f"conceded is associated with **{model.params['GA']:.3f}** points "
                f"(holding the other constant). The model explains **{model.rsquared * 100:.1f}%** "
                f"of the variance in league points."
            )

        st.divider()
        st.subheader("Extended Model: Pts = β₀ + β₁·W + β₂·D + β₃·L + ε")

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
                "Variable": model2.params.index,
                "Coefficient": model2.params.values.round(4),
                "Std. Error": model2.bse.values.round(4),
                "t-value": model2.tvalues.values.round(4),
                "p-value": model2.pvalues.values.round(6),
            })
            st.dataframe(coef_df2.set_index("Variable"), use_container_width=True)

            st.markdown(
                f"**Interpretation:** As expected, wins contribute ~3 points each "
                f"(coefficient ≈ {model2.params['W']:.2f}) and draws ~1 point "
                f"(coefficient ≈ {model2.params['D']:.2f}). This near-perfect R² "
                f"({model2.rsquared:.4f}) reflects the deterministic points system."
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
