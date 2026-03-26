import pandas as pd
import numpy as np
import statsmodels.api as sm
import os


def format_season_label(yr, season_type):
    if season_type == "split":
        return f"{yr - 1}-{str(yr)[2:]}"
    return str(yr)


def render_star_display(rating):
    filled = int(rating)
    empty = 5 - filled
    return '<span style="color: #FFD700; font-size: 1.3em;">' + ("&#9733;" * filled) + ("&#9734;" * empty) + "</span>"


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


def fit_ols_goals_model(df):
    """Fit OLS model: Pts ~ GF + GA. Returns fitted model or None."""
    required = {"Pts", "GF", "GA"}
    if not required.issubset(df.columns) or len(df) < 5:
        return None
    clean = df[list(required)].dropna()
    if len(clean) < 5:
        return None
    X = sm.add_constant(clean[["GF", "GA"]])
    y = clean["Pts"]
    return sm.OLS(y, X).fit()


def predict_points(model, gf, ga):
    """Predict points for given goals scored and conceded."""
    if model is None:
        return None
    new_X = pd.DataFrame({"const": [1.0], "GF": [gf], "GA": [ga]})
    pred = model.predict(new_X)
    return float(pred.iloc[0])


def bayesian_penalty_conversion(taker_rate, gk_save_rate, league_avg_rate=0.76, weight=10):
    """
    Bayesian shrinkage estimate of penalty conversion probability.
    Blends taker's observed rate toward league average based on sample weight.
    """
    shrunk_taker = (taker_rate * weight + league_avg_rate * weight) / (2 * weight)
    gk_stop_prob = gk_save_rate
    return round(shrunk_taker * (1 - gk_stop_prob) + shrunk_taker * gk_stop_prob * 0.1, 4)


def load_fallback_penalty_data(league_name):
    """Load static fallback penalty CSVs for a cup/tournament when Transfermarkt is unreachable.
    Returns (takers_df, gks_df)."""
    cup_map = {
        "Champions League":            ("champions_league_takers.csv",  "champions_league_gks.csv"),
        "Europa League":               ("europa_league_takers.csv",      "europa_league_gks.csv"),
        "Conference League":           ("conference_league_takers.csv",  "conference_league_gks.csv"),
        "FIFA World Cup":              ("world_cup_takers.csv",          "world_cup_gks.csv"),
        "UEFA European Championship":  ("euros_takers.csv",              "euros_gks.csv"),
        "AFC Asian Cup":               ("asian_cup_takers.csv",          "asian_cup_gks.csv"),
        "Copa América":                ("copa_america_takers.csv",       "copa_america_gks.csv"),
        "CONMEBOL Libertadores":       ("libertadores_takers.csv",       "libertadores_gks.csv"),
    }
    files = cup_map.get(league_name)
    if not files:
        return pd.DataFrame(), pd.DataFrame()
    cups_dir = os.path.join(os.path.dirname(__file__), "fallback_data", "cups")
    takers_path = os.path.join(cups_dir, files[0])
    gks_path    = os.path.join(cups_dir, files[1])
    takers = pd.read_csv(takers_path) if os.path.exists(takers_path) else pd.DataFrame()
    gks    = pd.read_csv(gks_path)    if os.path.exists(gks_path)    else pd.DataFrame()
    return takers, gks


def load_fallback_data(league_name):
    """Load static fallback CSV for a league when live scraping fails."""
    mapping = {
        "Premier League": "premier_league_2023_24.csv",
        "La Liga": "la_liga_2023_24.csv",
        "Bundesliga": "bundesliga_2023_24.csv",
        "Serie A": "serie_a_2023_24.csv",
        "Ligue 1": "ligue_1_2023_24.csv",
        "Eredivisie": "eredivisie_2023_24.csv",
        "Scottish Premiership": "scottish_premiership_2023_24.csv",
        "Saudi Pro League": "saudi_pro_league_2023_24.csv",
        "Indian Super League": "indian_super_league_2023_24.csv",
        "J1 League": "j1_league_2023.csv",
        "K League 1": "k_league_1_2023.csv",
        "Singapore Premier League": "singapore_premier_league_2023.csv",
        "MLS": "mls_2023.csv",
        "Brasileirão Série A": "brasileirao_2023.csv",
        "Argentine Primera División": "argentine_primera_2023.csv",
    }
    filename = mapping.get(league_name)
    if not filename:
        return pd.DataFrame()
    fallback_dir = os.path.join(os.path.dirname(__file__), "fallback_data")
    path = os.path.join(fallback_dir, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)
