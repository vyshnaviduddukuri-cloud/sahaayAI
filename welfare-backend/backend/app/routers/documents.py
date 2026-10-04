from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/checklist", response_model=schemas.DocumentChecklistOut)
def get_checklist(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Builds F10: a single, deduplicated document checklist across every
    scheme the user is currently eligible for, plus a per-scheme breakdown
    so the frontend can show "needed for: PM-KISAN, PMAY-G" under each item.
    """
    record = (
        db.query(models.EligibilityResult)
        .filter(models.EligibilityResult.user_id == user.id)
        .order_by(models.EligibilityResult.created_at.desc())
        .first()
    )
    if not record or not record.eligible:
        raise HTTPException(status_code=404, detail="No eligible schemes found. Run an eligibility check first.")

    all_docs: set[str] = set()
    per_scheme: dict[str, list[str]] = {}

    for scheme in record.eligible:
        name = scheme.get("name", scheme.get("scheme_id", "Unknown scheme"))
        docs = scheme.get("documents", [])
        per_scheme[name] = docs
        all_docs.update(docs)

    return schemas.DocumentChecklistOut(documents=sorted(all_docs), per_scheme=per_scheme)
