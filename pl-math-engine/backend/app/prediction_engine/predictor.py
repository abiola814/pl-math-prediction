"""Core scoreline predictor — ported from pldashboard predict_v2.py PredictorV2.

This is the heart of the prediction system. It builds a probability distribution
over all possible scorelines using historical frequency analysis.

Algorithm (from predict_v2.py):
1. Build scoreline frequency dicts for both teams (all seasons)
2. Separate home-only / away-only subsets
3. Get head-to-head scoreline frequency
4. Merge: base = home_all + away_all (minus duplicate H2H)
5. Layer in home-specific at 0.2x weight
6. Layer in away-specific at 0.2x weight
7. Layer in H2H at 0.4x weight
8. Scale by form (home_form, 0.5, away_form) for W/D/L scorelines
9. Normalize to probabilities
"""

from typing import Optional

import numpy as np

from app.config import settings
from app.data.form_calculator import FormCalculator
from app.models.fixture import Fixture
from app.prediction_engine.scoreline import Scoreline


class ScorelinePredictor:
    HOME_AWAY_WEIGHTING = settings.HOME_AWAY_WEIGHTING  # 0.2
    FIXTURE_WEIGHTING = settings.FIXTURE_WEIGHTING      # 0.4

    def __init__(
        self,
        team_ratings: dict[str, float],
        home_advantages: dict[str, float],
    ):
        self.team_ratings = team_ratings
        self.home_advantages = home_advantages
        self.form_calculator = FormCalculator()

    # ── Frequency Building ─────────────────────────────────────────

    @staticmethod
    def _build_team_freq(
        team_name: str,
        fixtures: list[Fixture],
        as_home_team: str | None = None,
    ) -> dict[Scoreline, int]:
        """Build scoreline frequency dict for a team's historical results.

        All scorelines are normalized so the specified home team is always
        on the 'home' side. If as_home_team is None, uses actual positions.
        """
        freq: dict[Scoreline, int] = {}
        for fix in fixtures:
            if fix.home_goals is None or fix.away_goals is None:
                continue

            hg, ag = fix.home_goals, fix.away_goals
            is_home = fix.home_team_name == team_name

            # If we need to normalize so as_home_team is always home
            if as_home_team and not is_home:
                # Flip the scoreline so 'team_name' appears as home
                hg, ag = ag, hg

            scoreline = Scoreline(hg, ag)
            freq[scoreline] = freq.get(scoreline, 0) + 1

        return freq

    @staticmethod
    def _build_home_only_freq(
        team_name: str, fixtures: list[Fixture]
    ) -> dict[Scoreline, int]:
        """Scorelines only from matches where team played at home."""
        freq: dict[Scoreline, int] = {}
        for fix in fixtures:
            if fix.home_goals is None or fix.home_team_name != team_name:
                continue
            s = Scoreline(fix.home_goals, fix.away_goals)
            freq[s] = freq.get(s, 0) + 1
        return freq

    @staticmethod
    def _build_away_only_freq(
        team_name: str, fixtures: list[Fixture], as_home_team: str | None = None
    ) -> dict[Scoreline, int]:
        """Scorelines only from matches where team played away.

        If as_home_team is provided, scorelines are flipped so the specified
        team appears as the home team.
        """
        freq: dict[Scoreline, int] = {}
        for fix in fixtures:
            if fix.away_goals is None or fix.away_team_name != team_name:
                continue
            if as_home_team:
                # Flip: the away team's goals become home, and vice versa
                s = Scoreline(fix.away_goals, fix.home_goals)
            else:
                s = Scoreline(fix.home_goals, fix.away_goals)
            freq[s] = freq.get(s, 0) + 1
        return freq

    @staticmethod
    def _build_h2h_freq(
        home_team: str, away_team: str, fixtures: list[Fixture]
    ) -> dict[Scoreline, int]:
        """Scorelines from head-to-head matches, normalized to home_team as home."""
        freq: dict[Scoreline, int] = {}
        for fix in fixtures:
            if fix.home_goals is None or fix.away_goals is None:
                continue
            is_right_way = (
                fix.home_team_name == home_team and fix.away_team_name == away_team
            )
            is_reversed = (
                fix.home_team_name == away_team and fix.away_team_name == home_team
            )
            if not (is_right_way or is_reversed):
                continue

            if is_right_way:
                s = Scoreline(fix.home_goals, fix.away_goals)
            else:
                s = Scoreline(fix.away_goals, fix.home_goals)
            freq[s] = freq.get(s, 0) + 1
        return freq

    # ── Frequency Operations ───────────────────────────────────────

    @staticmethod
    def _merge_freq(
        freq1: dict[Scoreline, float], freq2: dict[Scoreline, float]
    ) -> dict[Scoreline, float]:
        merged: dict[Scoreline, float] = {}
        for f in (freq1, freq2):
            for s, count in f.items():
                merged[s] = merged.get(s, 0) + count
        return merged

    @staticmethod
    def _add_scaled(
        freq: dict[Scoreline, float],
        insert: dict[Scoreline, float],
        scale: float,
    ):
        for s, count in insert.items():
            freq[s] = freq.get(s, 0) + count * scale

    @staticmethod
    def _subtract_scaled(
        freq: dict[Scoreline, float],
        sub: dict[Scoreline, float],
        scale: float = 1.0,
    ):
        for s, count in sub.items():
            if s in freq:
                freq[s] -= count * scale

    @staticmethod
    def _scale_by_result(
        freq: dict[Scoreline, float],
        scale: tuple[float, float, float],
    ):
        """Scale frequencies by result type: (home_win_scale, draw_scale, away_win_scale)."""
        home_s, draw_s, away_s = scale
        for s in freq:
            if s.home_goals > s.away_goals:
                freq[s] *= home_s
            elif s.home_goals < s.away_goals:
                freq[s] *= away_s
            else:
                freq[s] *= draw_s

    @staticmethod
    def _normalize(freq: dict[Scoreline, float]) -> dict[Scoreline, float]:
        """Convert frequencies to probabilities."""
        total = sum(freq.values())
        if total <= 0:
            return {}
        return {s: count / total for s, count in freq.items()}

    # ── Main Prediction ────────────────────────────────────────────

    def compute_scoreline_probabilities(
        self,
        home_team: str,
        away_team: str,
        home_fixtures: list[Fixture],
        away_fixtures: list[Fixture],
        h2h_fixtures: list[Fixture],
        home_form: float,
        away_form: float,
        odds: Optional[tuple[float, float, float]] = None,
    ) -> dict[Scoreline, float]:
        """Full PredictorV2 algorithm — returns scoreline probability distribution.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_fixtures: All historical fixtures for home team
            away_fixtures: All historical fixtures for away team
            h2h_fixtures: Head-to-head fixtures between these two teams
            home_form: Home team form [0, 1]
            away_form: Away team form [0, 1]
            odds: Optional (home_prob, draw_prob, away_prob) from bookmakers

        Returns:
            {Scoreline: probability} dict
        """
        # Step 1: Build all-time scoreline frequencies for each team
        # Normalized so home_team is always the home side
        home_all_freq = self._build_team_freq(home_team, home_fixtures, as_home_team=home_team)
        away_all_freq = self._build_team_freq(away_team, away_fixtures, as_home_team=home_team)

        # Step 2: Home-only and away-only subsets
        home_home_freq = self._build_home_only_freq(home_team, home_fixtures)
        away_away_freq = self._build_away_only_freq(away_team, away_fixtures, as_home_team=home_team)

        # Step 3: H2H frequency (already normalized to home_team as home)
        h2h_freq = self._build_h2h_freq(home_team, away_team, h2h_fixtures)

        # Step 4: Merge base — all results from both teams
        # This creates duplicates for H2H matches (present in both sets)
        freq: dict[Scoreline, float] = self._merge_freq(
            {s: float(c) for s, c in home_all_freq.items()},
            {s: float(c) for s, c in away_all_freq.items()},
        )

        # Step 5: Remove one copy of H2H duplicates
        self._subtract_scaled(freq, {s: float(c) for s, c in h2h_freq.items()})

        # Step 6: Layer in home-specific scorelines at 0.2x
        self._add_scaled(freq, {s: float(c) for s, c in home_home_freq.items()}, self.HOME_AWAY_WEIGHTING)

        # Step 7: Layer in away-specific scorelines at 0.2x
        self._add_scaled(freq, {s: float(c) for s, c in away_away_freq.items()}, self.HOME_AWAY_WEIGHTING)

        # Step 8: Layer in H2H at 0.4x
        self._add_scaled(freq, {s: float(c) for s, c in h2h_freq.items()}, self.FIXTURE_WEIGHTING)

        # Step 9: Form scaling
        form_scale = (home_form, 0.5, away_form)

        # Step 10: Optionally blend with odds
        if odds:
            scale = tuple(f / 2 + o / 2 for f, o in zip(form_scale, odds))
        else:
            scale = form_scale

        self._scale_by_result(freq, scale)

        # Step 11: Remove any negative frequencies (from subtraction)
        freq = {s: max(0, c) for s, c in freq.items()}

        # Step 12: Normalize to probabilities
        return self._normalize(freq)

    @staticmethod
    def predict_score(scoreline_probs: dict[Scoreline, float]) -> Scoreline | None:
        """Pick the maximum-likelihood scoreline."""
        if not scoreline_probs:
            return None
        return max(scoreline_probs, key=scoreline_probs.get)

    @staticmethod
    def top_scorelines(
        scoreline_probs: dict[Scoreline, float], n: int = 5
    ) -> list[tuple[Scoreline, float]]:
        """Return the top N most likely scorelines."""
        sorted_probs = sorted(scoreline_probs.items(), key=lambda x: x[1], reverse=True)
        return sorted_probs[:n]
