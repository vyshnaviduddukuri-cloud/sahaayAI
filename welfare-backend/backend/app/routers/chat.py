import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.utils.security import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatOut)
async def chat(
    data: schemas.ChatIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Thin proxy to the AI service's RAG-grounded chat agent (F9). Sends the
    user's saved profile along so the agent can answer questions like
    "why don't I qualify for X" without re-asking basic details.
    """
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()

    try:
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/chat",
                json={
                    "message": data.message,
                    "language": data.language or user.preferred_language,
                    "profile": profile.to_ai_payload() if profile else {},
                },
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Chat assistant unavailable. Try again shortly.")

    return schemas.ChatOut(reply=result.get("reply", ""), sources=result.get("sources", []))
