"""Cron job endpoint — called by external scheduler to refresh predictions.

Protect with CRON_SECRET so only authorized callers can trigger a refresh.
Usage:
  curl -X POST https://your-api.com/cron/refresh \
       -H "Authorization: Bearer YOUR_CRON_SECRET"
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.prediction_engine.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["cron"])


def _verify_cron_secret(request: Request):
    """Verify the cron secret from Authorization header."""
    if not settings.CRON_SECRET:
        raise HTTPException(
            status_code=503,
            detail="CRON_SECRET not configured. Set it in .env.",
        )
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if token != settings.CRON_SECRET:
        raise HTTPException(status_code=401, detail="Invalid cron secret")


@router.post("/refresh")
async def cron_refresh(
    request: Request,
    db: Session = Depends(get_db),
):
    """Refresh all data and regenerate predictions.

    Called by external cron scheduler (e.g. cron-job.org, Railway cron).
    Requires Authorization: Bearer <CRON_SECRET> header.
    """
    _verify_cron_secret(request)

    logger.info("Cron refresh triggered")
    service = PredictionService(db)

    # Refresh data from API-Football
    await service.data_service.refresh_all()

    # Update actuals for completed matches
    await service.update_actuals()

    # Generate new predictions
    predictions = await service.predict_upcoming()

    logger.info(f"Cron refresh complete — {len(predictions)} predictions generated")

    return {
        "status": "success",
        "predictions_generated": len(predictions),
    }
