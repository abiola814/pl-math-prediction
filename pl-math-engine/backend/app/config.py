from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API-Football (direct dashboard — v3.football.api-sports.io)
    API_FOOTBALL_KEY: str = ""
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Database
    DATABASE_URL: str = "sqlite:///./pl_math_engine.db"

    # Season
    CURRENT_SEASON: int = 2024
    NUM_SEASONS: int = 4
    PREMIER_LEAGUE_ID: int = 39

    # Prediction algorithm constants (from pldashboard)
    HOME_AWAY_WEIGHTING: float = 0.2
    FIXTURE_WEIGHTING: float = 0.4
    FORM_MATCH_COUNT: int = 20
    FORM_WEIGHT_MIN: float = 0.2
    FORM_WEIGHT_MAX: float = 1.0
    SEASON_RATING_MULTIPLIER: float = 2.5
    GAMES_THRESHOLD: int = 4
    HOME_GAMES_THRESHOLD: int = 6
    PANDEMIC_YEAR: int = 2020

    # LLM adjustment bounds
    LLM_MAX_ADJUSTMENT: float = 0.15

    # Corner prediction
    CORNER_HOME_ADVANTAGE_FACTOR: float = 1.15

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
