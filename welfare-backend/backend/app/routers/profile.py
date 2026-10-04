import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.utils.security import get_current_user
from app.extractor_fallback import extract_profile as local_extract_profile

logger = logging.getLogger("profile")
router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=schemas.ProfileOut)
def get_profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("", response_model=schemas.ProfileOut)
def update_profile(
    data: schemas.ProfileIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Direct field edit -- used by the manual form (F1 in your feature list)."""
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    if not profile:
        profile = models.Profile(user_id=user.id)
        db.add(profile)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/intake", response_model=schemas.ProfileOut)
async def intake_from_text(
    data: schemas.IntakeTextIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Multilingual voice/text intake (F7). Tries the AI service's /extract
    first (richer, handles more phrasing). If that's unreachable or
    returns something unusable, falls back to a local keyword-based
    extractor so this never hard-fails during a demo -- same pattern as
    /eligibility/check.
    """
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    if not profile:
        profile = models.Profile(user_id=user.id)
        db.add(profile)
        db.commit()

    profile.raw_intake_text = data.text
    extracted = {}
    engine_used = "ai_service"

    try:
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/extract",
                json={"text": data.text, "language": data.language or user.preferred_language},
            )
            resp.raise_for_status()
            result = resp.json()
            extracted = result.get("profile", {})
            if not extracted:
                raise ValueError("AI service returned an empty profile")
    except (httpx.HTTPError, ValueError) as e:
        logger.warning(f"AI service /extract unavailable ({e}), falling back to local extractor.")
        extracted = local_extract_profile(data.text)
        engine_used = "local_fallback"

    for field, value in extracted.items():
        if value is not None and hasattr(profile, field):
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    logger.info(f"Intake via {engine_used}: extracted {list(extracted.keys())}")
    return profile