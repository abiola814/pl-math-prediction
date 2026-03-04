"""Tests for form calculator."""

from datetime import datetime

from app.data.form_calculator import FormCalculator
from app.models.fixture import Fixture


def _make_fixture(home: str, away: str, hg: int, ag: int, days_ago: int = 0) -> Fixture:
    f = Fixture()
    f.api_id = hash(f"{home}{away}{hg}{ag}{days_ago}") % 100000
    f.home_team_name = home
    f.away_team_name = away
    f.home_goals = hg
    f.away_goals = ag
    f.date = datetime(2024, 6, 1)
    f.status = "FT"
    return f


class TestFormCalculator:
    def test_neutral_form_with_no_matches(self):
        calc = FormCalculator()
        form = calc.calc_form("TeamA", [], {"TeamA": 0.5, "TeamB": 0.5})
        assert form == 0.5

    def test_winning_increases_form(self):
        calc = FormCalculator()
        fixtures = [
            _make_fixture("TeamA", "TeamB", 3, 0),
            _make_fixture("TeamA", "TeamC", 2, 0),
            _make_fixture("TeamD", "TeamA", 0, 2),
        ]
        ratings = {"TeamA": 0.8, "TeamB": 0.6, "TeamC": 0.5, "TeamD": 0.4}
        form = calc.calc_form("TeamA", fixtures, ratings)
        assert form > 0.5

    def test_losing_decreases_form(self):
        calc = FormCalculator()
        fixtures = [
            _make_fixture("TeamA", "TeamB", 0, 3),
            _make_fixture("TeamC", "TeamA", 2, 0),
        ]
        ratings = {"TeamA": 0.5, "TeamB": 0.7, "TeamC": 0.6}
        form = calc.calc_form("TeamA", fixtures, ratings)
        assert form < 0.5

    def test_form_clamped_to_0_1(self):
        calc = FormCalculator()
        # Huge wins against strong teams
        fixtures = [_make_fixture("TeamA", "TeamB", 10, 0) for _ in range(20)]
        ratings = {"TeamA": 0.5, "TeamB": 1.0}
        form = calc.calc_form("TeamA", fixtures, ratings)
        assert 0.0 <= form <= 1.0

    def test_opposition_strength_matters(self):
        calc = FormCalculator()
        # Same result but against different strength opponents
        fixtures_vs_strong = [_make_fixture("TeamA", "Strong", 2, 1)]
        fixtures_vs_weak = [_make_fixture("TeamA", "Weak", 2, 1)]

        ratings = {"TeamA": 0.5, "Strong": 0.9, "Weak": 0.1}

        form_vs_strong = calc.calc_form("TeamA", fixtures_vs_strong, ratings)
        form_vs_weak = calc.calc_form("TeamA", fixtures_vs_weak, ratings)

        # Beating a strong team should give higher form
        assert form_vs_strong > form_vs_weak
