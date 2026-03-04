import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.data.api_football import APIFootballClient
from app.models.fixture import Fixture
from app.models.fixture_stats import FixtureStatistics
from app.models.injury import Injury
from app.models.standing import Standing
from app.models.team import Team

logger = logging.getLogger(__name__)


class DataService:
    """Orchestrates data fetching from API-Football and caching to DB."""

    def __init__(self, db: Session, api_client: APIFootballClient = None):
        self.db = db
        self.api = api_client or APIFootballClient()

    # ── Teams ──────────────────────────────────────────────────────

    async def refresh_teams(self, season: int = settings.CURRENT_SEASON):
        """Fetch and cache all PL teams for a season."""
        raw_teams = await self.api.get_teams(season=season)
        count = 0
        for entry in raw_teams:
            team_data = entry.get("team", {})
            api_id = team_data.get("id")
            if not api_id:
                continue
            existing = self.db.query(Team).filter(Team.api_id == api_id).first()
            if existing:
                existing.name = team_data.get("name", existing.name)
                existing.short_name = team_data.get("code", existing.short_name)
                existing.logo_url = team_data.get("logo", existing.logo_url)
            else:
                self.db.add(Team(
                    api_id=api_id,
                    name=team_data.get("name", ""),
                    short_name=team_data.get("code", ""),
                    logo_url=team_data.get("logo", ""),
                    league_id=settings.PREMIER_LEAGUE_ID,
                ))
                count += 1
        self.db.commit()
        logger.info(f"Teams: refreshed ({count} new)")

    # ── Fixtures ───────────────────────────────────────────────────

    async def refresh_fixtures(self, season: int):
        """Fetch and cache all fixtures for a season."""
        raw_fixtures = await self.api.get_fixtures(season=season)
        count = 0
        for entry in raw_fixtures:
            fix = entry.get("fixture", {})
            teams = entry.get("teams", {})
            goals = entry.get("goals", {})
            league = entry.get("league", {})
            api_id = fix.get("id")
            if not api_id:
                continue

            existing = self.db.query(Fixture).filter(Fixture.api_id == api_id).first()
            date_str = fix.get("date", "")
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                date = datetime.utcnow()

            status = fix.get("status", {}).get("short", "NS")
            home_goals = goals.get("home")
            away_goals = goals.get("away")

            if existing:
                existing.status = status
                existing.home_goals = home_goals
                existing.away_goals = away_goals
                existing.date = date
            else:
                self.db.add(Fixture(
                    api_id=api_id,
                    home_team_id=teams.get("home", {}).get("id", 0),
                    away_team_id=teams.get("away", {}).get("id", 0),
                    home_team_name=teams.get("home", {}).get("name", ""),
                    away_team_name=teams.get("away", {}).get("name", ""),
                    date=date,
                    matchday=league.get("round", "").split(" - ")[-1] if league.get("round") else None,
                    season=season,
                    league_id=settings.PREMIER_LEAGUE_ID,
                    status=status,
                    home_goals=home_goals,
                    away_goals=away_goals,
                ))
                count += 1
        self.db.commit()
        logger.info(f"Fixtures {season}: refreshed ({count} new)")

    # ── Fixture Statistics (corners, shots, etc.) ──────────────────

    async def refresh_fixture_statistics(self, season: int):
        """Fetch and cache statistics for all completed fixtures in a season."""
        finished = (
            self.db.query(Fixture)
            .filter(Fixture.season == season, Fixture.status == "FT")
            .all()
        )
        count = 0
        for fixture in finished:
            already = (
                self.db.query(FixtureStatistics)
                .filter(FixtureStatistics.fixture_api_id == fixture.api_id)
                .first()
            )
            if already:
                continue

            stats_list = await self.api.get_fixture_statistics(fixture.api_id)
            for team_stats in stats_list:
                team = team_stats.get("team", {})
                stats = {
                    s["type"]: s["value"]
                    for s in team_stats.get("statistics", [])
                }
                self.db.add(FixtureStatistics(
                    fixture_api_id=fixture.api_id,
                    team_api_id=team.get("id", 0),
                    corners=self._parse_int(stats.get("Corner Kicks")),
                    shots_on_target=self._parse_int(stats.get("Shots on Goal")),
                    shots_total=self._parse_int(stats.get("Total Shots")),
                    possession=self._parse_float(stats.get("Ball Possession")),
                    fouls=self._parse_int(stats.get("Fouls")),
                    yellow_cards=self._parse_int(stats.get("Yellow Cards")),
                    red_cards=self._parse_int(stats.get("Red Cards")),
                ))
                count += 1
        self.db.commit()
        logger.info(f"Fixture stats {season}: refreshed ({count} new stat rows)")

    # ── Standings ──────────────────────────────────────────────────

    async def refresh_standings(self, season: int):
        """Fetch and cache league standings for a season."""
        raw = await self.api.get_standings(season=season)
        # Clear old standings for this season
        self.db.query(Standing).filter(Standing.season == season).delete()
        for entry in raw:
            team = entry.get("team", {})
            all_stats = entry.get("all", {})
            home_stats = entry.get("home", {})
            away_stats = entry.get("away", {})
            self.db.add(Standing(
                team_api_id=team.get("id", 0),
                team_name=team.get("name", ""),
                season=season,
                position=entry.get("rank", 0),
                played=all_stats.get("played", 0),
                won=all_stats.get("win", 0),
                drawn=all_stats.get("draw", 0),
                lost=all_stats.get("lose", 0),
                goals_for=all_stats.get("goals", {}).get("for", 0),
                goals_against=all_stats.get("goals", {}).get("against", 0),
                goal_difference=entry.get("goalsDiff", 0),
                points=entry.get("points", 0),
                home_won=home_stats.get("win", 0),
                home_drawn=home_stats.get("draw", 0),
                home_lost=home_stats.get("lose", 0),
                away_won=away_stats.get("win", 0),
                away_drawn=away_stats.get("draw", 0),
                away_lost=away_stats.get("lose", 0),
            ))
        self.db.commit()
        logger.info(f"Standings {season}: refreshed")

    # ── Injuries ───────────────────────────────────────────────────

    async def refresh_injuries(self):
        """Fetch and cache current injuries for all PL teams."""
        # Clear old injuries
        self.db.query(Injury).delete()
        raw = await self.api.get_injuries()
        count = 0
        for entry in raw:
            player = entry.get("player", {})
            team = entry.get("team", {})
            player_name = player.get("name")
            if not player_name:
                continue
            self.db.add(Injury(
                team_api_id=team.get("id", 0),
                team_name=team.get("name", ""),
                player_name=player_name,
                player_position=player.get("type", ""),
                injury_type=player.get("reason", ""),
                reason=player.get("reason", ""),
                fetched_at=datetime.utcnow(),
            ))
            count += 1
        self.db.commit()
        logger.info(f"Injuries: refreshed ({count} entries)")

    # ── Full Refresh ───────────────────────────────────────────────

    async def refresh_all(self, current_season: int = settings.CURRENT_SEASON):
        """Full data refresh across multiple seasons."""
        await self.refresh_teams(current_season)
        for offset in range(settings.NUM_SEASONS):
            season = current_season - offset
            await self.refresh_fixtures(season)
            await self.refresh_standings(season)
        await self.refresh_fixture_statistics(current_season)
        await self.refresh_injuries()
        logger.info("Full data refresh complete")

    # ── Query Helpers ──────────────────────────────────────────────

    def get_upcoming_fixtures(self) -> list[Fixture]:
        return (
            self.db.query(Fixture)
            .filter(Fixture.status == "NS", Fixture.season == settings.CURRENT_SEASON)
            .order_by(Fixture.date)
            .all()
        )

    def get_finished_fixtures(self, season: int) -> list[Fixture]:
        return (
            self.db.query(Fixture)
            .filter(Fixture.status == "FT", Fixture.season == season)
            .order_by(Fixture.date)
            .all()
        )

    def get_team_fixtures(self, team_name: str, num_seasons: int = settings.NUM_SEASONS) -> list[Fixture]:
        min_season = settings.CURRENT_SEASON - num_seasons + 1
        return (
            self.db.query(Fixture)
            .filter(
                Fixture.status == "FT",
                Fixture.season >= min_season,
                (Fixture.home_team_name == team_name) | (Fixture.away_team_name == team_name),
            )
            .order_by(Fixture.date)
            .all()
        )

    def get_h2h_fixtures(self, team1: str, team2: str) -> list[Fixture]:
        min_season = settings.CURRENT_SEASON - settings.NUM_SEASONS + 1
        return (
            self.db.query(Fixture)
            .filter(
                Fixture.status == "FT",
                Fixture.season >= min_season,
                (
                    ((Fixture.home_team_name == team1) & (Fixture.away_team_name == team2))
                    | ((Fixture.home_team_name == team2) & (Fixture.away_team_name == team1))
                ),
            )
            .order_by(Fixture.date)
            .all()
        )

    def get_standings_multi_season(self) -> dict[int, list[Standing]]:
        result = {}
        for offset in range(settings.NUM_SEASONS):
            season = settings.CURRENT_SEASON - offset
            result[season] = (
                self.db.query(Standing)
                .filter(Standing.season == season)
                .order_by(Standing.position)
                .all()
            )
        return result

    def get_team_injuries(self, team_name: str) -> list[Injury]:
        return (
            self.db.query(Injury)
            .filter(Injury.team_name == team_name)
            .all()
        )

    def get_corner_stats(self, team_api_id: int) -> list[FixtureStatistics]:
        return (
            self.db.query(FixtureStatistics)
            .filter(FixtureStatistics.team_api_id == team_api_id)
            .all()
        )

    # ── Utility ────────────────────────────────────────────────────

    @staticmethod
    def _parse_int(value) -> int | None:
        if value is None:
            return None
        try:
            return int(str(value).replace("%", ""))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace("%", ""))
        except (ValueError, TypeError):
            return None
