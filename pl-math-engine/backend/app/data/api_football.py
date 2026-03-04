import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class APIFootballClient:
    """Client for API-Football v3 (direct dashboard)."""

    def __init__(
        self,
        api_key: str = settings.API_FOOTBALL_KEY,
        base_url: str = settings.API_FOOTBALL_BASE_URL,
    ):
        self.base_url = base_url
        self.headers = {
            "x-apisports-key": api_key,
        }

    async def _get(self, endpoint: str, params: dict) -> dict:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{endpoint}"
            response = await client.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("errors"):
                logger.error(f"API-Football error: {data['errors']}")
            return data

    async def get_fixtures(
        self, season: int, league_id: int = settings.PREMIER_LEAGUE_ID
    ) -> list[dict]:
        """Get all fixtures for a PL season."""
        data = await self._get("fixtures", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_fixture_by_id(self, fixture_id: int) -> Optional[dict]:
        """Get a single fixture by API ID."""
        data = await self._get("fixtures", {"id": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None

    async def get_fixture_statistics(self, fixture_id: int) -> list[dict]:
        """Get match statistics (corners, shots, etc.) for a fixture."""
        data = await self._get("fixtures/statistics", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_standings(
        self, season: int, league_id: int = settings.PREMIER_LEAGUE_ID
    ) -> list[dict]:
        """Get league standings for a season."""
        data = await self._get("standings", {"league": league_id, "season": season})
        response = data.get("response", [])
        if response and response[0].get("league", {}).get("standings"):
            return response[0]["league"]["standings"][0]
        return []

    async def get_injuries(
        self, league_id: int = settings.PREMIER_LEAGUE_ID, season: int = settings.CURRENT_SEASON
    ) -> list[dict]:
        """Get current injuries for all teams in the league."""
        data = await self._get("injuries", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_team_injuries(self, team_id: int) -> list[dict]:
        """Get current injuries for a specific team."""
        data = await self._get(
            "injuries",
            {"team": team_id, "season": settings.CURRENT_SEASON},
        )
        return data.get("response", [])

    async def get_odds(self, fixture_id: int) -> list[dict]:
        """Get bookmaker odds for a fixture."""
        data = await self._get("odds", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_teams(
        self, league_id: int = settings.PREMIER_LEAGUE_ID, season: int = settings.CURRENT_SEASON
    ) -> list[dict]:
        """Get all teams in a league for a season."""
        data = await self._get("teams", {"league": league_id, "season": season})
        return data.get("response", [])
