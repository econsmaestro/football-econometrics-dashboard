"""
Unit tests for core model functions in the Football Econometrics Dashboard.
Run with: python -m pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import (
    format_season_label,
    render_star_display,
    rebase_to_standard_season,
    fit_ols_goals_model,
    predict_points,
    bayesian_penalty_conversion,
    load_fallback_data,
)


# ---------------------------------------------------------------------------
# format_season_label
# ---------------------------------------------------------------------------

class TestFormatSeasonLabel:
    def test_split_season_formats_correctly(self):
        assert format_season_label(2024, "split") == "2023-24"

    def test_split_season_2000(self):
        assert format_season_label(2000, "split") == "1999-00"

    def test_calendar_season_returns_year_string(self):
        assert format_season_label(2024, "calendar") == "2024"

    def test_calendar_season_2019(self):
        assert format_season_label(2019, "calendar") == "2019"


# ---------------------------------------------------------------------------
# render_star_display
# ---------------------------------------------------------------------------

class TestRenderStarDisplay:
    def test_five_stars_all_filled(self):
        result = render_star_display(5)
        assert result.count("&#9733;") == 5
        assert result.count("&#9734;") == 0

    def test_one_star_one_filled_four_empty(self):
        result = render_star_display(1)
        assert result.count("&#9733;") == 1
        assert result.count("&#9734;") == 4

    def test_three_stars_correct_split(self):
        result = render_star_display(3)
        assert result.count("&#9733;") == 3
        assert result.count("&#9734;") == 2

    def test_output_is_html_span(self):
        result = render_star_display(4)
        assert result.startswith("<span")
        assert result.endswith("</span>")

    def test_total_stars_always_five(self):
        for rating in range(1, 6):
            result = render_star_display(rating)
            total = result.count("&#9733;") + result.count("&#9734;")
            assert total == 5, f"Expected 5 total stars for rating {rating}, got {total}"


# ---------------------------------------------------------------------------
# rebase_to_standard_season
# ---------------------------------------------------------------------------

class TestRebaseToStandardSeason:
    def _make_season_df(self, pld, pts, season_end=2000):
        return pd.DataFrame({
            "Squad": ["Team A", "Team B", "Team C"],
            "Pld": [pld] * 3,
            "Pts": [pts, pts - 10, pts - 20],
            "W": [pld // 3] * 3,
            "D": [2] * 3,
            "L": [1] * 3,
            "GF": [50, 40, 30],
            "GA": [30, 40, 50],
            "GD": [20, 0, -20],
            "Season_End": [season_end] * 3,
        })

    def test_no_rebase_when_pld_matches_standard(self):
        df = self._make_season_df(pld=38, pts=80)
        result = rebase_to_standard_season(df, games_per_season=38)
        assert (result["Rebased"] == False).all()
        assert list(result["Pts"]) == list(df["Pts"])

    def test_rebase_scales_up_pts_proportionally(self):
        df = self._make_season_df(pld=34, pts=68)
        result = rebase_to_standard_season(df, games_per_season=38)
        assert result["Rebased"].iloc[0] == True
        assert result["Pld"].iloc[0] == 38
        expected_pts = round(68 * 38 / 34)
        assert result["Pts"].iloc[0] == expected_pts

    def test_empty_dataframe_returns_unchanged(self):
        df = pd.DataFrame()
        result = rebase_to_standard_season(df, games_per_season=38)
        assert result.empty

    def test_no_rebase_when_games_per_season_is_zero(self):
        df = self._make_season_df(pld=38, pts=80)
        result = rebase_to_standard_season(df, games_per_season=0)
        assert list(result["Pts"]) == list(df["Pts"])

    def test_incomplete_season_not_rebased(self):
        df = pd.DataFrame({
            "Squad": ["Team A", "Team B", "Team C"],
            "Pld": [20, 19, 21],
            "Pts": [40, 35, 30],
            "Season_End": [2024, 2024, 2024],
        })
        result = rebase_to_standard_season(df, games_per_season=38)
        assert (result["Rebased"] == False).all()

    def test_rebase_gf_ga_scaled_with_pts(self):
        df = self._make_season_df(pld=34, pts=68)
        result = rebase_to_standard_season(df, games_per_season=38)
        expected_gf = round(50 * 38 / 34)
        assert result["GF"].iloc[0] == expected_gf


# ---------------------------------------------------------------------------
# OLS regression model
# ---------------------------------------------------------------------------

class TestOLSModel:
    def _premier_league_like_df(self):
        np.random.seed(42)
        n = 20
        gf = np.random.randint(30, 100, n)
        ga = np.random.randint(20, 80, n)
        pts = (gf * 0.7 - ga * 0.5 + 50 + np.random.randn(n) * 5).clip(10, 100)
        return pd.DataFrame({"GF": gf, "GA": ga, "Pts": pts})

    def test_model_fits_without_error(self):
        df = self._premier_league_like_df()
        model = fit_ols_goals_model(df)
        assert model is not None

    def test_gf_coefficient_is_positive(self):
        df = self._premier_league_like_df()
        model = fit_ols_goals_model(df)
        assert model.params["GF"] > 0, "Scoring more goals should be positively linked to points"

    def test_ga_coefficient_is_negative(self):
        df = self._premier_league_like_df()
        model = fit_ols_goals_model(df)
        assert model.params["GA"] < 0, "Conceding more goals should be negatively linked to points"

    def test_r_squared_reasonable(self):
        df = self._premier_league_like_df()
        model = fit_ols_goals_model(df)
        assert model.rsquared > 0.5, f"R² should be > 0.5, got {model.rsquared:.2f}"

    def test_model_returns_none_for_insufficient_data(self):
        df = pd.DataFrame({"GF": [1, 2], "GA": [1, 2], "Pts": [1, 2]})
        model = fit_ols_goals_model(df)
        assert model is None

    def test_prediction_increases_with_more_goals(self):
        df = self._premier_league_like_df()
        model = fit_ols_goals_model(df)
        pts_low = predict_points(model, gf=40, ga=50)
        pts_high = predict_points(model, gf=80, ga=30)
        assert pts_high > pts_low, "More goals scored and fewer conceded should predict more points"


# ---------------------------------------------------------------------------
# Bayesian penalty predictor
# ---------------------------------------------------------------------------

class TestBayesianPenaltyConversion:
    def test_output_is_between_zero_and_one(self):
        result = bayesian_penalty_conversion(0.80, 0.20)
        assert 0.0 <= result <= 1.0

    def test_better_taker_higher_probability(self):
        elite = bayesian_penalty_conversion(0.90, 0.15)
        average = bayesian_penalty_conversion(0.70, 0.15)
        assert elite > average

    def test_better_goalkeeper_lowers_probability(self):
        easy_gk = bayesian_penalty_conversion(0.80, 0.10)
        hard_gk = bayesian_penalty_conversion(0.80, 0.35)
        assert easy_gk > hard_gk

    def test_output_is_rounded_to_4_decimals(self):
        result = bayesian_penalty_conversion(0.76, 0.20)
        assert result == round(result, 4)


# ---------------------------------------------------------------------------
# Fallback data loader
# ---------------------------------------------------------------------------

class TestLoadFallbackData:
    def test_premier_league_fallback_loads(self):
        df = load_fallback_data("Premier League")
        assert not df.empty, "Premier League fallback CSV should load"

    def test_fallback_has_required_columns(self):
        df = load_fallback_data("Premier League")
        for col in ("Pos", "Squad", "Pld", "Pts", "GF", "GA"):
            assert col in df.columns, f"Column '{col}' missing from fallback data"

    def test_fallback_has_20_teams(self):
        df = load_fallback_data("Premier League")
        assert len(df) == 20

    def test_unknown_league_returns_empty(self):
        df = load_fallback_data("Made Up League FC")
        assert df.empty

    def test_la_liga_fallback_loads(self):
        df = load_fallback_data("La Liga")
        assert not df.empty

    def test_bundesliga_fallback_has_18_teams(self):
        df = load_fallback_data("Bundesliga")
        assert len(df) == 18

    def test_pts_column_is_numeric(self):
        df = load_fallback_data("Serie A")
        assert pd.api.types.is_numeric_dtype(df["Pts"]), "Pts column should be numeric"
