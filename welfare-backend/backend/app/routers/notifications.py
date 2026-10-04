from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

# --------------------------------------------------------------------------
# PM-KISAN and other scheme notifications: for a hackathon, there is no
# public push-notification API from the government to subscribe to. Two
# honest options, in order of demo-readiness:
#
#   1. SEED DATA (what's wired up below) -- a small set of realistic,
#      clearly-labeled sample notifications ("PM-KISAN 18th installment
#      released", "PMAY-G survey deadline extended") so the feature is
#      fully visible and functional in the demo.
#   2. REAL FEED (v2, if you have hours to spare) -- a scheduled job that
#      periodically scrapes/checks the PM-KISAN beneficiary status page or
#      any RSS/news feed the ministry publishes, and inserts rows into the
#      `notifications` table below. The route and schema don't change either
#      way -- only where the rows come from.
# --------------------------------------------------------------------------

SEED_NOTIFICATIONS = [
    {
        "scheme_id": "pm_kisan",
        "title": "PM-KISAN: 18th installment released",
        "message": "The 18th installment of ₹2,000 has been credited to eligible farmer accounts. "
                    "Check your status on the PM-KISAN portal using your registered Aadhaar number.",
    },
    {
        "scheme_id": "pm_kisan",
        "title": "PM-KISAN: e-KYC deadline reminder",
        "message": "Farmers who haven't completed mandatory e-KYC risk missing the next installment. "
                    "Complete it via OTP on the PM-KISAN portal or at your nearest CSC center.",
    },
    {
        "scheme_id": "nsap_widow",
        "title": "NSAP: pension disbursal schedule updated",
        "message": "This quarter's widow pension disbursal has moved to the last week of the month.",
    },
]


@router.get("", response_model=List[schemas.NotificationOut])
def list_notifications(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns notifications relevant to the user: broadcast ones (user_id is
    null) plus any addressed specifically to them. Seeds demo data on first
    call so the feature is visible without a separate ingest step.
    """
    existing = db.query(models.Notification).count()
    if existing == 0:
        for n in SEED_NOTIFICATIONS:
            db.add(models.Notification(user_id=None, **n))
        db.commit()

    return (
        db.query(models.Notification)
        .filter((models.Notification.user_id == user.id) | (models.Notification.user_id.is_(None)))
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}
