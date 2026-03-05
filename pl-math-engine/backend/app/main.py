"""PL Math Engine — FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.accuracy import router as accuracy_router
from app.api.fixtures import router as fixtures_router
from app.api.predictions import router as predictions_router
from app.api.results import router as results_router
from app.api.standings import router as standings_router
from app.api.teams import router as teams_router
from app.database import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="PL Math Engine",
    description="Premier League match prediction API with score, over/under, BTTS, and corner predictions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://prempredict.3gensolution.co.uk",
        "https://www.prempredict.3gensolution.co.uk",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions_router)
app.include_router(fixtures_router)
app.include_router(accuracy_router)
app.include_router(standings_router)
app.include_router(teams_router)
app.include_router(results_router)


@app.on_event("startup")
def startup():
    create_tables()
    logging.info("PL Math Engine started — tables created")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pl-math-engine"}
