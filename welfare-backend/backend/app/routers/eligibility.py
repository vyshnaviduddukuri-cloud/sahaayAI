import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.utils.security import get_current_user
from app.rules_engine import check_eligibility as local_check_eligibility

logger = logging.getLogger("eligibility")
router = APIRouter(prefix="/eligibility", tags=["eligibility"])


def _is_valid_result(result: dict) -> bool:
    """Guards against a malformed or empty response from the AI service --
    e.g. missing keys, wrong types, or a silently-empty result that would
    otherwise make the demo look broken for no visible reason."""
    if not isinstance(result, dict):
        return False
    for key in ("eligible", "nearly_eligible", "ineligible"):
        if key not in result or not isinstance(result[key], list):
            return False
    return True


async def _run_ai_service_check(payload: dict):
    """Returns the AI service's result, or None if it's unreachable, slow,
    or returns something malformed -- never raises, so the caller can fall
    back cleanly."""
    try:
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{settings.AI_SERVICE_URL}/check", json=payload)
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError as e:
        logger.warning(f"AI service /check unreachable or failed: {e}")
        return None
    except ValueError as e:
        logger.warning(f"AI service /check returned invalid JSON: {e}")
        return None

    if not _is_valid_result(result):
        logger.warning(f"AI service /check returned an unexpected shape: {result}")
        return None

    return result


@router.post("/check", response_model=schemas.EligibilityCheckOut)
async def check_eligibility(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tries the AI service's rules engine first (richer, RAG-aware). If it's
    unreachable, times out, or returns something malformed, falls back to
    the local deterministic engine (app/rules_engine.py) so this feature
    NEVER hard-fails during a demo. The response always carries an
    `engine_used` field so you always know which one actually answered.
    """
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile before checking eligibility")

    payload = profile.to_ai_payload()
    payload["language"] = user.preferred_language
    logger.info(f"Checking eligibility for user {user.id} with profile: {payload}")

    result = await _run_ai_service_check(payload)
    engine_used = "ai_service"

    if result is None:
        logger.info("Falling back to local rules engine.")
        result = local_check_eligibility(payload, language=user.preferred_language)
        engine_used = "local_fallback"

    record = models.EligibilityResult(
        user_id=user.id,
        eligible=result.get("eligible", []),
        nearly_eligible=result.get("nearly_eligible", []),
        ineligible=result.get("ineligible", []),
    )
    db.add(record)
    db.commit()

    logger.info(
        f"Eligibility check complete via {engine_used}: "
        f"{len(record.eligible)} eligible, {len(record.nearly_eligible)} nearly eligible"
    )

    return schemas.EligibilityCheckOut(
        eligible=record.eligible,
        nearly_eligible=record.nearly_eligible,
        ineligible=record.ineligible,
        checked_at=record.created_at,
        engine_used=engine_used,
    )


@router.get("/latest", response_model=schemas.EligibilityCheckOut)
def latest_result(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read-only: last cached result, so the frontend can reload the dashboard cheaply."""
    record = (
        db.query(models.EligibilityResult)
        .filter(models.EligibilityResult.user_id == user.id)
        .order_by(models.EligibilityResult.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No eligibility check has been run yet")
    return schemas.EligibilityCheckOut(
        eligible=record.eligible,
        nearly_eligible=record.nearly_eligible,
        ineligible=record.ineligible,
        checked_at=record.created_at,
        engine_used=None,
    )


@router.get("/schemes")
def list_all_schemes():
    """
    Public catalog of every scheme the local engine knows about -- powers
    the frontend's homepage slider with real data instead of a hardcoded
    placeholder array.
    """
    from app.data.schemes import SCHEMES
    return [
        {
            "scheme_id": s["scheme_id"],
            "name": s["name"],
            "benefit": s["benefit"],
            "description": s["description"],
        }
        for s in SCHEMES
    ]