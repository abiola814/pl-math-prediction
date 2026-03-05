"""Team dashboard API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.data.data_service import DataService
from app.data.form_calculator import FormCalculator
from app.data.home_advantages import HomeAdvantageCalculator
from app.data.team_ratings import TeamRatingCalculator
from app.database import get_db
from app.models.fixture import Fixture
from app.models.standing import Standing
from app.models.team import Team
from app.schemas.dashboard import (
    AllTeamsTimeSeries,
    FormHistoryPoint,
    GoalFrequency,
    GoalsAnalysis,
    InjuryItem,
    MiniTableRow,
    OpponentInfo,
    ScorelineFrequencyItem,
    SpiderAttribute,
    TeamComparisonData,
    TeamDashboardResponse,
    TeamFixtureResult,
    TeamMatchdaySnapshot,
)
from app.schemas.prediction import FixtureResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


def _fixture_to_team_result(fix: Fixture, team_name: str) -> TeamFixtureResult:
    """Convert a Fixture to a TeamFixtureResult from a team's perspective."""
    is_home = fix.home_team_name == team_name
    if is_home:
        goals_for = fix.home_goals or 0
        goals_against = fix.away_goals or 0
        opponent = fix.away_team_name
    else:
        goals_for = fix.away_goals or 0
        goals_against = fix.home_goals or 0
        opponent = fix.home_team_name

    if goals_for > goals_against:
        result = "W"
    elif goals_for < goals_against:
        result = "L"
    else:
        result = "D"

    return TeamFixtureResult(
        date=fix.date,
        opponent=opponent,
        is_home=is_home,
        goals_for=goals_for,
        goals_against=goals_against,
        result=result,
        matchday=fix.matchday,
    )


def _compute_goals_analysis(
    fixtures: list[TeamFixtureResult],
) -> GoalsAnalysis:
    """Compute goals analysis from a list of team fixture results."""
    if not fixtures:
        return GoalsAnalysis(
            avg_scored=0, avg_conceded=0,
            avg_scored_home=0, avg_scored_away=0,
            avg_conceded_home=0, avg_conceded_away=0,
            clean_sheets=0, failed_to_score=0, total_matches=0,
        )

    home_matches = [f for f in fixtures if f.is_home]
    away_matches = [f for f in fixtures if not f.is_home]

    total_scored = sum(f.goals_for for f in fixtures)
    total_conceded = sum(f.goals_against for f in fixtures)
    home_scored = sum(f.goals_for for f in home_matches)
    home_conceded = sum(f.goals_against for f in home_matches)
    away_scored = sum(f.goals_for for f in away_matches)
    away_conceded = sum(f.goals_against for f in away_matches)

    n = len(fixtures)
    n_home = len(home_matches) or 1
    n_away = len(away_matches) or 1

    return GoalsAnalysis(
        avg_scored=round(total_scored / n, 2),
        avg_conceded=round(total_conceded / n, 2),
        avg_scored_home=round(home_scored / n_home, 2),
        avg_scored_away=round(away_scored / n_away, 2),
        avg_conceded_home=round(home_conceded / n_home, 2),
        avg_conceded_away=round(away_conceded / n_away, 2),
        clean_sheets=sum(1 for f in fixtures if f.goals_against == 0),
        failed_to_score=sum(1 for f in fixtures if f.goals_for == 0),
        total_matches=n,
    )


# ── All-Teams Time Series (Form/Position/Points over matchdays) ──
# NOTE: This static route MUST be defined before /{team_name}/... routes

def _build_team_matchday_data(
    team_name: str, fixtures: list[Fixture],
) -> list[dict]:
    """Build matchday-by-matchday stats for a single team."""
    team_fixes = [
        f for f in fixtures
        if (f.home_team_name == team_name or f.away_team_name == team_name)
        and f.status == "FT"
    ]
    team_fixes.sort(key=lambda f: f.date)

    snapshots = []
    cum_points = 0
    recent_pts: list[int] = []

    for i, fix in enumerate(team_fixes):
        is_home = fix.home_team_name == team_name
        scored = (fix.home_goals or 0) if is_home else (fix.away_goals or 0)
        conceded = (fix.away_goals or 0) if is_home else (fix.home_goals or 0)

        if scored > conceded:
            pts = 3
        elif scored == conceded:
            pts = 1
        else:
            pts = 0

        cum_points += pts
        recent_pts.append(pts)
        window = recent_pts[-5:]
        form_val = sum(window) / (len(window) * 3) if window else 0.5

        matchday = fix.matchday or (i + 1)
        snapshots.append({
            "matchday": matchday,
            "form": round(form_val, 3),
            "cumulative_points": cum_points,
            "position": 0,  # filled in later
        })

    return snapshots


@router.get("/analysis/time-series", response_model=AllTeamsTimeSeries)
async def get_all_teams_time_series(db: Session = Depends(get_db)):
    """Return form, cumulative points, and position for all 20 teams across matchdays."""
    all_fixtures = (
        db.query(Fixture)
        .filter(Fixture.season == settings.CURRENT_SEASON, Fixture.status == "FT")
        .order_by(Fixture.date)
        .all()
    )

    standings = (
        db.query(Standing)
        .filter(Standing.season == settings.CURRENT_SEASON)
        .order_by(Standing.position)
        .all()
    )
    team_names = [s.team_name for s in standings]

    teams_data: dict[str, list[dict]] = {}
    for tn in team_names:
        teams_data[tn] = _build_team_matchday_data(tn, all_fixtures)

    # Compute positions at each matchday
    all_matchdays = set()
    for tn, snaps in teams_data.items():
        for s in snaps:
            all_matchdays.add(s["matchday"])

    for md in sorted(all_matchdays):
        team_pts = []
        for tn in team_names:
            snaps = teams_data[tn]
            snap = next((s for s in snaps if s["matchday"] == md), None)
            if snap:
                team_pts.append((tn, snap["cumulative_points"], snap["form"]))
            else:
                prev = [s for s in snaps if s["matchday"] < md]
                if prev:
                    team_pts.append((tn, prev[-1]["cumulative_points"], prev[-1]["form"]))
                else:
                    team_pts.append((tn, 0, 0.5))

        team_pts.sort(key=lambda x: (-x[1], -x[2]))

        for pos, (tn, _, _) in enumerate(team_pts, 1):
            snap = next((s for s in teams_data[tn] if s["matchday"] == md), None)
            if snap:
                snap["position"] = pos

    result_teams = {}
    for tn in team_names:
        result_teams[tn] = [
            TeamMatchdaySnapshot(
                matchday=s["matchday"],
                form=s["form"],
                cumulative_points=s["cumulative_points"],
                position=s["position"],
            )
            for s in teams_data[tn]
        ]

    return AllTeamsTimeSeries(teams=result_teams)


# ── Dynamic team routes ──────────────────────────────────────

@router.get("/{team_name}/dashboard", response_model=TeamDashboardResponse)
async def get_team_dashboard(team_name: str, db: Session = Depends(get_db)):
    """Return all dashboard data for a single team."""
    service = DataService(db)

    # Find standing for this team
    standing = (
        db.query(Standing)
        .filter(Standing.team_name == team_name, Standing.season == settings.CURRENT_SEASON)
        .first()
    )
    if not standing:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found in current season standings")

    # Get team logo
    team_record = db.query(Team).filter(Team.api_id == standing.team_api_id).first()
    logo_url = team_record.logo_url if team_record else None

    # Compute ratings, form, home advantage
    standings_by_season = service.get_standings_multi_season()
    team_ratings = TeamRatingCalculator().compute(standings_by_season, settings.CURRENT_SEASON)

    fixtures_by_season = {}
    for offset in range(settings.NUM_SEASONS):
        season = settings.CURRENT_SEASON - offset
        fixtures_by_season[season] = service.get_finished_fixtures(season)

    home_advantages = HomeAdvantageCalculator().compute(fixtures_by_season, settings.CURRENT_SEASON)

    team_fixtures = service.get_team_fixtures(team_name)
    form_val = FormCalculator().calc_form(team_name, team_fixtures, team_ratings)

    # Current season fixtures only
    season_fixtures_raw = [
        f for f in team_fixtures if f.season == settings.CURRENT_SEASON
    ]
    season_fixtures = [_fixture_to_team_result(f, team_name) for f in season_fixtures_raw]

    # Recent form (last 5)
    recent_form = season_fixtures[-5:] if season_fixtures else []

    # Goals analysis from current season
    goals_analysis = _compute_goals_analysis(season_fixtures)

    # Injuries
    injuries_raw = service.get_team_injuries(team_name)
    injuries = [
        InjuryItem(
            player_name=inj.player_name,
            player_position=inj.player_position,
            reason=inj.reason,
        )
        for inj in injuries_raw
    ]

    # Next fixture
    next_fix = (
        db.query(Fixture)
        .filter(
            Fixture.status == "NS",
            Fixture.season == settings.CURRENT_SEASON,
            (Fixture.home_team_name == team_name) | (Fixture.away_team_name == team_name),
        )
        .order_by(Fixture.date)
        .first()
    )

    # Build mini league table (8 rows centered on current team)
    current_standings = standings_by_season.get(settings.CURRENT_SEASON, [])
    current_standings_sorted = sorted(current_standings, key=lambda s: s.position)
    logo_by_api_id = {t.api_id: t.logo_url for t in db.query(Team).all()}

    team_idx = next(
        (i for i, s in enumerate(current_standings_sorted) if s.team_name == team_name),
        0,
    )
    # Show 3 above and 4 below, adjusted at boundaries
    start = max(0, team_idx - 3)
    end = min(len(current_standings_sorted), start + 8)
    if end - start < 8:
        start = max(0, end - 8)

    mini_table = [
        MiniTableRow(
            position=s.position,
            team_name=s.team_name,
            logo_url=logo_by_api_id.get(s.team_api_id),
            goal_difference=s.goal_difference,
            points=s.points,
            is_current=(s.team_name == team_name),
        )
        for s in current_standings_sorted[start:end]
    ]

    # Next fixture + opponent info
    next_fixture_resp = None
    next_opponent_info = None
    h2h_results = []
    if next_fix:
        next_fixture_resp = FixtureResponse(
            api_id=next_fix.api_id,
            home_team=next_fix.home_team_name,
            away_team=next_fix.away_team_name,
            home_team_id=next_fix.home_team_id,
            away_team_id=next_fix.away_team_id,
            date=next_fix.date,
            status=next_fix.status,
            home_goals=next_fix.home_goals,
            away_goals=next_fix.away_goals,
            matchday=next_fix.matchday,
            season=next_fix.season,
        )
        # H2H vs next opponent
        opponent = (
            next_fix.away_team_name
            if next_fix.home_team_name == team_name
            else next_fix.home_team_name
        )
        h2h_raw = service.get_h2h_fixtures(team_name, opponent)
        h2h_results = [_fixture_to_team_result(f, team_name) for f in h2h_raw]

        # Opponent info
        opp_standing = next(
            (s for s in current_standings_sorted if s.team_name == opponent), None
        )
        if opp_standing:
            form_calc = FormCalculator()
            opp_fixtures = service.get_team_fixtures(opponent)
            opp_form = form_calc.calc_form(opponent, opp_fixtures, team_ratings)
            next_opponent_info = OpponentInfo(
                name=opponent,
                position=opp_standing.position,
                form=round(opp_form, 3),
                rating=round(team_ratings.get(opponent, 0.0), 3),
            )

    return TeamDashboardResponse(
        team_name=team_name,
        team_api_id=standing.team_api_id,
        logo_url=logo_url,
        position=standing.position,
        points=standing.points,
        played=standing.played,
        won=standing.won,
        drawn=standing.drawn,
        lost=standing.lost,
        goals_for=standing.goals_for,
        goals_against=standing.goals_against,
        goal_difference=standing.goal_difference,
        rating=round(team_ratings.get(team_name, 0.0), 3),
        form=round(form_val, 3),
        home_advantage=round(home_advantages.get(team_name, 0.0), 3),
        recent_form=recent_form,
        season_fixtures=season_fixtures,
        injuries=injuries,
        goals_analysis=goals_analysis,
        next_fixture=next_fixture_resp,
        next_opponent_info=next_opponent_info,
        h2h_vs_next=h2h_results,
        mini_table=mini_table,
    )


@router.get("/{team_name}/form-history", response_model=list[FormHistoryPoint])
async def get_team_form_history(team_name: str, db: Session = Depends(get_db)):
    """Return matchday-by-matchday form and cumulative stats for charts."""
    service = DataService(db)

    # Get current season finished fixtures for this team
    all_fixtures = service.get_team_fixtures(team_name, num_seasons=1)
    season_fixtures = [
        f for f in all_fixtures if f.season == settings.CURRENT_SEASON and f.status == "FT"
    ]

    if not season_fixtures:
        return []

    # Sort by date
    season_fixtures.sort(key=lambda f: f.date)

    result = []
    cum_points = 0
    cum_gf = 0
    cum_ga = 0
    # Rolling 5-match form
    recent_results: list[int] = []  # points per match

    for i, fix in enumerate(season_fixtures):
        is_home = fix.home_team_name == team_name
        if is_home:
            scored = fix.home_goals or 0
            conceded = fix.away_goals or 0
        else:
            scored = fix.away_goals or 0
            conceded = fix.home_goals or 0

        if scored > conceded:
            match_points = 3
        elif scored == conceded:
            match_points = 1
        else:
            match_points = 0

        cum_points += match_points
        cum_gf += scored
        cum_ga += conceded

        # Rolling 5-match form (percentage of max possible points)
        recent_results.append(match_points)
        window = recent_results[-5:]
        form_val = sum(window) / (len(window) * 3) if window else 0.5

        matchday = fix.matchday or (i + 1)

        result.append(FormHistoryPoint(
            matchday=matchday,
            form=round(form_val, 3),
            cumulative_points=cum_points,
            goals_scored=scored,
            goals_conceded=conceded,
            cumulative_goals_for=cum_gf,
            cumulative_goals_against=cum_ga,
        ))

    return result


# ── Goal Frequency Distribution ──

@router.get("/{team_name}/goal-frequency", response_model=GoalFrequency)
async def get_goal_frequency(team_name: str, db: Session = Depends(get_db)):
    """Return goals scored/conceded frequency distribution for a team vs league avg."""
    # Get current season fixtures for all teams
    all_fixtures = (
        db.query(Fixture)
        .filter(Fixture.season == settings.CURRENT_SEASON, Fixture.status == "FT")
        .all()
    )

    standings = (
        db.query(Standing)
        .filter(Standing.season == settings.CURRENT_SEASON)
        .all()
    )
    team_names = [s.team_name for s in standings]

    max_goals = 5  # 0,1,2,3,4,5+

    def count_goals(tn: str) -> tuple[list[int], list[int]]:
        scored_counts = [0] * (max_goals + 1)
        conceded_counts = [0] * (max_goals + 1)
        for f in all_fixtures:
            if f.home_team_name == tn:
                s = min(f.home_goals or 0, max_goals)
                c = min(f.away_goals or 0, max_goals)
                scored_counts[s] += 1
                conceded_counts[c] += 1
            elif f.away_team_name == tn:
                s = min(f.away_goals or 0, max_goals)
                c = min(f.home_goals or 0, max_goals)
                scored_counts[s] += 1
                conceded_counts[c] += 1
        return scored_counts, conceded_counts

    # Team data
    team_scored, team_conceded = count_goals(team_name)
    team_total = sum(team_scored) or 1
    team_scored_pct = [round(c / team_total * 100, 1) for c in team_scored]
    team_conceded_pct = [round(c / team_total * 100, 1) for c in team_conceded]

    # League average
    avg_scored = [0.0] * (max_goals + 1)
    avg_conceded = [0.0] * (max_goals + 1)
    for tn in team_names:
        sc, cc = count_goals(tn)
        total = sum(sc) or 1
        for i in range(max_goals + 1):
            avg_scored[i] += (sc[i] / total * 100)
            avg_conceded[i] += (cc[i] / total * 100)
    n_teams = len(team_names) or 1
    avg_scored_pct = [round(v / n_teams, 1) for v in avg_scored]
    avg_conceded_pct = [round(v / n_teams, 1) for v in avg_conceded]

    return GoalFrequency(
        goals=list(range(max_goals + 1)),
        team_scored_pct=team_scored_pct,
        team_conceded_pct=team_conceded_pct,
        avg_scored_pct=avg_scored_pct,
        avg_conceded_pct=avg_conceded_pct,
    )


# ── Scoreline Frequency ──

@router.get("/{team_name}/scoreline-frequency", response_model=list[ScorelineFrequencyItem])
async def get_scoreline_frequency(team_name: str, db: Session = Depends(get_db)):
    """Return scoreline frequencies for a team vs league average."""
    all_fixtures = (
        db.query(Fixture)
        .filter(Fixture.season == settings.CURRENT_SEASON, Fixture.status == "FT")
        .all()
    )

    standings = (
        db.query(Standing)
        .filter(Standing.season == settings.CURRENT_SEASON)
        .all()
    )
    team_names = [s.team_name for s in standings]

    def get_scorelines(tn: str) -> dict[str, tuple[int, str]]:
        """Returns {scoreline: (count, outcome)} from team perspective."""
        scores: dict[str, tuple[int, str]] = {}
        for f in all_fixtures:
            if f.home_team_name == tn:
                gf, ga = f.home_goals or 0, f.away_goals or 0
            elif f.away_team_name == tn:
                gf, ga = f.away_goals or 0, f.home_goals or 0
            else:
                continue

            key = f"{gf}-{ga}"
            outcome = "W" if gf > ga else ("D" if gf == ga else "L")
            count, _ = scores.get(key, (0, outcome))
            scores[key] = (count + 1, outcome)
        return scores

    # Team scorelines
    team_scores = get_scorelines(team_name)
    team_total = sum(c for c, _ in team_scores.values()) or 1

    # League average scorelines
    all_scores: dict[str, int] = {}
    for tn in team_names:
        for key, (count, _) in get_scorelines(tn).items():
            all_scores[key] = all_scores.get(key, 0) + count
    avg_total = sum(all_scores.values()) / (len(team_names) or 1)

    # Build results sorted by team frequency descending
    all_keys = set(list(team_scores.keys()) + list(all_scores.keys()))
    items = []
    for key in all_keys:
        team_count, outcome = team_scores.get(key, (0, "D"))
        # Determine outcome from scoreline if team doesn't have it
        if key not in team_scores:
            parts = key.split("-")
            gf, ga = int(parts[0]), int(parts[1])
            outcome = "W" if gf > ga else ("D" if gf == ga else "L")
        avg_count = all_scores.get(key, 0) / (len(team_names) or 1)
        items.append(ScorelineFrequencyItem(
            scoreline=key,
            team_pct=round(team_count / team_total * 100, 1),
            avg_pct=round(avg_count / (avg_total or 1) * 100, 1),
            outcome=outcome,
        ))

    items.sort(key=lambda x: -x.team_pct)
    return items[:15]  # Top 15 scorelines


# ── Team Comparison Spider/Radar Chart ──

@router.get("/{team_name}/comparison", response_model=TeamComparisonData)
async def get_team_comparison(team_name: str, db: Session = Depends(get_db)):
    """Return spider/radar chart data: Attack, Defence, Clean Sheets, Consistency, Win Streak, vs Big 6."""
    service = DataService(db)

    standings = (
        db.query(Standing)
        .filter(Standing.season == settings.CURRENT_SEASON)
        .all()
    )
    team_names = [s.team_name for s in standings]
    standing_map = {s.team_name: s for s in standings}

    all_fixtures = (
        db.query(Fixture)
        .filter(Fixture.season == settings.CURRENT_SEASON, Fixture.status == "FT")
        .all()
    )

    BIG_6 = {"Manchester United", "Liverpool", "Manchester City", "Arsenal", "Chelsea", "Tottenham"}

    # Compute raw values for each team
    raw: dict[str, dict[str, float]] = {tn: {} for tn in team_names}

    for tn in team_names:
        team_fixes = [
            f for f in all_fixtures
            if f.home_team_name == tn or f.away_team_name == tn
        ]
        played = len(team_fixes) or 1

        # Attack: goals per game
        total_scored = 0
        total_conceded = 0
        clean_sheets = 0
        consistency = 0
        win_streak = 0
        temp_streak = 0
        prev_result = None
        big6_pts = 0
        big6_played = 0

        for f in sorted(team_fixes, key=lambda x: x.date):
            is_home = f.home_team_name == tn
            scored = (f.home_goals or 0) if is_home else (f.away_goals or 0)
            conceded = (f.away_goals or 0) if is_home else (f.home_goals or 0)
            opponent = f.away_team_name if is_home else f.home_team_name

            total_scored += scored
            total_conceded += conceded

            # Clean sheets
            if conceded == 0:
                clean_sheets += 1

            # Result
            if scored > conceded:
                result = "W"
            elif scored == conceded:
                result = "D"
            else:
                result = "L"

            # Consistency: back-to-back same results
            if prev_result is not None and prev_result == result:
                consistency += 1
            prev_result = result

            # Win streak
            if result == "W":
                temp_streak += 1
                win_streak = max(win_streak, temp_streak)
            else:
                temp_streak = 0

            # Vs Big 6
            if opponent in BIG_6:
                big6_played += 1
                if result == "W":
                    big6_pts += 3
                elif result == "D":
                    big6_pts += 1

        raw[tn]["attack"] = total_scored / played
        raw[tn]["defence"] = total_conceded / played  # lower = better
        raw[tn]["clean_sheets"] = clean_sheets
        raw[tn]["consistency"] = consistency
        raw[tn]["win_streak"] = win_streak
        raw[tn]["vs_big6"] = big6_pts / big6_played if big6_played > 0 else 0

    # Scale to 0-100
    def scale_values(attr: str, invert: bool = False) -> dict[str, float]:
        vals = [raw[tn][attr] for tn in team_names]
        mn, mx = min(vals), max(vals)
        spread = mx - mn if mx != mn else 1.0
        result = {}
        for tn in team_names:
            scaled = ((raw[tn][attr] - mn) / spread) * 100
            result[tn] = (100 - scaled) if invert else scaled
        return result

    attack_scaled = scale_values("attack")
    defence_scaled = scale_values("defence", invert=True)  # Lower conceded = higher score
    cs_scaled = scale_values("clean_sheets")
    consist_scaled = scale_values("consistency")
    streak_scaled = scale_values("win_streak")
    big6_scaled = scale_values("vs_big6")

    # Build response
    attr_names = ["Attack", "Defence", "Clean Sheets", "Consistency", "Win Streak", "vs Big 6"]
    all_scaled = [attack_scaled, defence_scaled, cs_scaled, consist_scaled, streak_scaled, big6_scaled]

    attributes = []
    for name, scaled_dict in zip(attr_names, all_scaled):
        team_val = scaled_dict.get(team_name, 50)
        avg_val = sum(scaled_dict.values()) / len(scaled_dict)
        attributes.append(SpiderAttribute(
            name=name,
            team_value=round(team_val, 1),
            avg_value=round(avg_val, 1),
        ))

    return TeamComparisonData(team_name=team_name, attributes=attributes)
