from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=schemas.ApplicationOut)
def create_application(
    data: schemas.ApplicationIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User marks a scheme as 'I'm applying for this' -- starts status tracking."""
    app_row = models.Application(
        user_id=user.id,
        scheme_id=data.scheme_id,
        scheme_name=data.scheme_name,
        reference_number=data.reference_number,
        submitted_office=data.submitted_office,
        notes=data.notes,
        status="submitted" if data.reference_number else "draft",
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return app_row


@router.get("", response_model=List[schemas.ApplicationOut])
def list_applications(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    This is your status-checking portal (the feature you mentioned): a
    single dashboard of every scheme the user applied to and where each
    one stands. Real government portals for PM-KISAN etc. generally don't
    expose a public status API, so for the hackathon this is a
    self-reported / manually-updated tracker rather than a live scrape --
    say that plainly if judges ask ("real portal integration is a v2 item
    behind official API access").
    """
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == user.id)
        .order_by(models.Application.updated_at.desc())
        .all()
    )


@router.patch("/{application_id}/status", response_model=schemas.ApplicationOut)
def update_status(
    application_id: str,
    data: schemas.ApplicationStatusUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = (
        db.query(models.Application)
        .filter(models.Application.id == application_id, models.Application.user_id == user.id)
        .first()
    )
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")

    valid_statuses = {"draft", "submitted", "under_review", "approved", "rejected"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")

    app_row.status = data.status
    if data.reference_number:
        app_row.reference_number = data.reference_number
    if data.notes:
        app_row.notes = data.notes
    db.commit()
    db.refresh(app_row)
    return app_row
