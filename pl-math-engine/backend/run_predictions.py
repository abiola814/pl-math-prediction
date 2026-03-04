#!/usr/bin/env python3
"""Standalone prediction runner — run separately from the API server.

Usage:
    python run_predictions.py              # Fetch data + generate predictions
    python run_predictions.py --refresh    # Force full data refresh first
    python run_predictions.py --schedule   # Run daily at 8 AM automatically

This script:
1. Refreshes data from API-Football (fixtures, standings, stats, injuries)
2. Generates predictions for all upcoming matches
3. Stores everything in the SQLite database
4. The API server (uvicorn) reads from the same DB to serve predictions

Intended to run a day before matchday so predictions are ready.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

import anthropic

from app.config import settings
from app.database import SessionLocal, create_tables
from app.prediction_engine.prediction_service import PredictionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_predictions")


async def run(force_refresh: bool = False):
    """Main prediction pipeline."""
    logger.info("=" * 60)
    logger.info("PL Math Engine — Prediction Runner")
    logger.info(f"Season: {settings.CURRENT_SEASON} | Time: {datetime.now()}")
    logger.info("=" * 60)

    # Create tables if they don't exist
    create_tables()

    # Open DB session
    db = SessionLocal()

    try:
        # Initialize Claude client if API key is available
        llm_client = None
        if settings.ANTHROPIC_API_KEY:
            llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info(f"LLM enabled (model: {settings.CLAUDE_MODEL})")
        else:
            logger.info("LLM disabled — no ANTHROPIC_API_KEY set")

        service = PredictionService(db, llm_client=llm_client)

        # Step 1: Refresh data from API-Football
        logger.info("")
        logger.info("--- Step 1: Refreshing data from API-Football ---")
        await service.data_service.refresh_all()

        # Step 2: Update actuals for completed matches
        logger.info("")
        logger.info("--- Step 2: Updating actuals for completed matches ---")
        await service.update_actuals()

        # Step 3: Generate predictions for upcoming fixtures
        logger.info("")
        logger.info("--- Step 3: Generating predictions ---")
        predictions = await service.predict_upcoming()

        # Step 4: Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"DONE — Generated {len(predictions)} predictions")
        logger.info("=" * 60)

        if predictions:
            logger.info("")
            logger.info("Upcoming predictions:")
            for p in predictions:
                score = p.predicted_score
                logger.info(
                    f"  {p.home_team} {score.home_goals}-{score.away_goals} {p.away_team} | "
                    f"{p.market.recommended_market} | "
                    f"{p.market.home_recommended} | {p.market.away_recommended} | "
                    f"Corners: {p.corners.recommended_pick} | "
                    f"Cards: {p.cards.recommended_pick}"
                )
        else:
            logger.info("No upcoming fixtures found.")

        # Step 5: Accuracy report
        accuracy = service.compute_accuracy()
        if accuracy.get("total_predictions", 0) > 0:
            logger.info("")
            logger.info("Accuracy report:")
            logger.info(f"  Total predictions: {accuracy['total_predictions']}")
            logger.info(f"  Exact score: {accuracy.get('exact_score_accuracy', 'N/A')}%")
            logger.info(f"  Correct result: {accuracy.get('result_accuracy', 'N/A')}%")
            logger.info(f"  Over/Under: {accuracy.get('over_under_accuracy', 'N/A')}%")
            logger.info(f"  BTTS: {accuracy.get('btts_accuracy', 'N/A')}%")
            logger.info(f"  Corner line: {accuracy.get('corner_line_accuracy', 'N/A')}%")
            logger.info(f"  Card line: {accuracy.get('card_line_accuracy', 'N/A')}%")

    except Exception as e:
        logger.error(f"Prediction run failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


def run_scheduled():
    """Run predictions on a daily schedule at 8 AM."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()

    def job():
        logger.info("Scheduled prediction run starting...")
        asyncio.run(run())

    # Run immediately on startup
    job()

    # Then schedule daily at 8 AM
    scheduler.add_job(job, "cron", hour=8, minute=0)
    logger.info("Scheduler active — next run at 8:00 AM daily")
    logger.info("Press Ctrl+C to stop")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PL Math Engine — Prediction Runner")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a daily schedule (8 AM) instead of once",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        asyncio.run(run())
