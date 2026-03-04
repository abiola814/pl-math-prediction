"""LLM market analyst — uses Claude to make direct over/under, BTTS, and corner calls.

Instead of weak multiplier adjustments, the LLM now:
1. Receives ALL the statistical data (score prediction, probabilities, corners, injuries, form)
2. Reasons about the MATCH CONTEXT (team style, injuries, matchup dynamics)
3. Makes its OWN over/under + BTTS + corner picks with reasoning
4. Its picks are shown alongside (or can override) the pure stats picks
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.data.corner_stats import CornerProfile
from app.models.injury import Injury
from app.prediction_engine.market_analyzer import MarketPrediction
from app.prediction_engine.card_predictor import CardPrediction
from app.prediction_engine.corner_predictor import CornerPrediction
from app.prediction_engine.scoreline import Scoreline

logger = logging.getLogger(__name__)


@dataclass
class LLMMarketVerdict:
    """The LLM's direct market calls."""
    # Over/Under for the match
    match_goals_pick: str         # e.g. "Over 2.5 Goals"
    match_goals_confidence: int   # 1-10 scale
    match_goals_reasoning: str

    # Home team over/under
    home_goals_pick: str          # e.g. "Over 1.5 Home Goals"
    home_goals_reasoning: str

    # Away team over/under
    away_goals_pick: str          # e.g. "Under 1.5 Away Goals"
    away_goals_reasoning: str

    # BTTS
    btts_pick: str                # "BTTS Yes" or "BTTS No"
    btts_confidence: int
    btts_reasoning: str

    # Corners
    corners_pick: str             # e.g. "Over 9.5 Corners"
    corners_confidence: int
    corners_reasoning: str

    # Cards (yellow)
    cards_pick: str               # e.g. "Over 3.5 Cards"
    cards_confidence: int
    cards_reasoning: str

    # Overall summary
    summary: str


class LLMMarketAnalyst:
    """Uses Claude to analyze match context and make market picks."""

    CACHE_TTL_SECONDS = 6 * 3600  # 6 hours

    def __init__(self, anthropic_client=None):
        self.client = anthropic_client
        self._cache: dict[str, tuple[float, LLMMarketVerdict]] = {}

    def _get_cached(self, cache_key: str) -> Optional[LLMMarketVerdict]:
        if cache_key in self._cache:
            timestamp, verdict = self._cache[cache_key]
            if time.time() - timestamp < self.CACHE_TTL_SECONDS:
                return verdict
            del self._cache[cache_key]
        return None

    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        predicted_score: Scoreline,
        stats_market: MarketPrediction,
        corners: CornerPrediction,
        cards: CardPrediction,
        home_injuries: list[Injury],
        away_injuries: list[Injury],
        home_form: float,
        away_form: float,
        home_rating: float,
        away_rating: float,
        top_scorelines: list[tuple[str, float]],
    ) -> LLMMarketVerdict:
        """Have Claude analyze the full match context and make market picks."""
        cache_key = f"{home_team}_v_{away_team}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if not self.client:
            return self._no_llm_verdict()

        try:
            prompt = self._build_prompt(
                home_team, away_team,
                predicted_score, stats_market, corners, cards,
                home_injuries, away_injuries,
                home_form, away_form,
                home_rating, away_rating,
                top_scorelines,
            )

            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            verdict = self._parse_response(text)
            self._cache[cache_key] = (time.time(), verdict)
            return verdict

        except Exception as e:
            logger.warning(f"LLM market analysis failed for {cache_key}: {e}")
            return self._no_llm_verdict()

    def _build_prompt(
        self,
        home_team: str,
        away_team: str,
        predicted_score: Scoreline,
        stats_market: MarketPrediction,
        corners: CornerPrediction,
        cards: CardPrediction,
        home_injuries: list[Injury],
        away_injuries: list[Injury],
        home_form: float,
        away_form: float,
        home_rating: float,
        away_rating: float,
        top_scorelines: list[tuple[str, float]],
    ) -> str:
        home_inj = self._format_injuries(home_injuries)
        away_inj = self._format_injuries(away_injuries)
        top_scores = ", ".join(f"{s} ({p:.0%})" for s, p in top_scorelines[:5])

        return f"""You are an expert football betting analyst. You have deep knowledge of Premier League teams, playing styles, managers, and tactical setups.

MATCH: {home_team} (HOME) vs {away_team} (AWAY)

=== STATISTICAL MODEL OUTPUT ===
Predicted score: {predicted_score.home_goals}-{predicted_score.away_goals}
Top scorelines: {top_scores}

Goal probabilities:
  Over 0.5: {stats_market.over_05:.0%} | Over 1.5: {stats_market.over_15:.0%}
  Over 2.5: {stats_market.over_25:.0%} | Over 3.5: {stats_market.over_35:.0%}
  BTTS Yes: {stats_market.btts_yes:.0%}

Stats recommendation: {stats_market.recommended_market} ({stats_market.recommended_confidence:.0%})
Stats BTTS: {stats_market.btts_recommendation} ({stats_market.btts_confidence:.0%})

Corner prediction: {corners.predicted_total:.1f} total (H: {corners.home_corners:.1f}, A: {corners.away_corners:.1f})
Corner pick: {corners.recommended_pick} ({corners.confidence:.0%})

Card prediction: {cards.predicted_total:.1f} yellow cards (H: {cards.home_cards:.1f}, A: {cards.away_cards:.1f})
Card pick: {cards.recommended_pick} ({cards.confidence:.0%})

=== TEAM CONTEXT ===
{home_team}: Rating {home_rating:.2f}/1.00 | Form {home_form:.2f}/1.00
{away_team}: Rating {away_rating:.2f}/1.00 | Form {away_form:.2f}/1.00

{home_team} injuries:
{home_inj if home_inj else "  None reported"}

{away_team} injuries:
{away_inj if away_inj else "  None reported"}

=== YOUR TASK ===
Using your knowledge of these teams' PLAYING STYLE, TACTICS, KEY PLAYERS, and the injury context above, make your market picks. Consider:
- Does this team play attacking/defensive football?
- Is the home team strong at home? Does the away team struggle away?
- Do missing players weaken the attack or defense specifically?
- Historical tendencies in this matchup
- Are both teams capable of scoring, or will one dominate?
- Is the referee strict? Are these teams physical/aggressive? (for card prediction)
- Do these teams have a rivalry or history of heated encounters?

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "match_goals_pick": "<Over/Under X.5 Goals>",
  "match_goals_confidence": <1-10>,
  "match_goals_reasoning": "<why>",
  "home_goals_pick": "<Over/Under X.5 Home Goals>",
  "home_goals_reasoning": "<why - can home team score 1, 2, or more?>",
  "away_goals_pick": "<Over/Under X.5 Away Goals>",
  "away_goals_reasoning": "<why - can away team score here?>",
  "btts_pick": "<BTTS Yes or BTTS No>",
  "btts_confidence": <1-10>,
  "btts_reasoning": "<why>",
  "corners_pick": "<Over/Under X.5 Corners>",
  "corners_confidence": <1-10>,
  "corners_reasoning": "<why>",
  "cards_pick": "<Over/Under X.5 Cards>",
  "cards_confidence": <1-10>,
  "cards_reasoning": "<why - consider team discipline, rivalry intensity, referee tendencies>",
  "summary": "<1-2 sentence overall match analysis>"
}}"""

    @staticmethod
    def _format_injuries(injuries: list[Injury]) -> str:
        if not injuries:
            return ""
        lines = []
        for inj in injuries[:10]:
            pos = inj.player_position or "Unknown"
            reason = inj.reason or inj.injury_type or "Unknown"
            lines.append(f"  - {inj.player_name} ({pos}) - {reason}")
        return "\n".join(lines)

    def _parse_response(self, text: str) -> LLMMarketVerdict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        data = json.loads(text)

        return LLMMarketVerdict(
            match_goals_pick=data.get("match_goals_pick", ""),
            match_goals_confidence=min(10, max(1, int(data.get("match_goals_confidence", 5)))),
            match_goals_reasoning=data.get("match_goals_reasoning", ""),
            home_goals_pick=data.get("home_goals_pick", ""),
            home_goals_reasoning=data.get("home_goals_reasoning", ""),
            away_goals_pick=data.get("away_goals_pick", ""),
            away_goals_reasoning=data.get("away_goals_reasoning", ""),
            btts_pick=data.get("btts_pick", ""),
            btts_confidence=min(10, max(1, int(data.get("btts_confidence", 5)))),
            btts_reasoning=data.get("btts_reasoning", ""),
            corners_pick=data.get("corners_pick", ""),
            corners_confidence=min(10, max(1, int(data.get("corners_confidence", 5)))),
            corners_reasoning=data.get("corners_reasoning", ""),
            cards_pick=data.get("cards_pick", ""),
            cards_confidence=min(10, max(1, int(data.get("cards_confidence", 5)))),
            cards_reasoning=data.get("cards_reasoning", ""),
            summary=data.get("summary", ""),
        )

    @staticmethod
    def _no_llm_verdict() -> LLMMarketVerdict:
        return LLMMarketVerdict(
            match_goals_pick="",
            match_goals_confidence=0,
            match_goals_reasoning="",
            home_goals_pick="",
            home_goals_reasoning="",
            away_goals_pick="",
            away_goals_reasoning="",
            btts_pick="",
            btts_confidence=0,
            btts_reasoning="",
            corners_pick="",
            corners_confidence=0,
            corners_reasoning="",
            cards_pick="",
            cards_confidence=0,
            cards_reasoning="",
            summary="",
        )
