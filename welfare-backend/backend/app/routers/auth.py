"""
Aadhaar-style verification, mocked for hackathon use.

Real UIDAI Aadhaar authentication requires an AUA/KUA license from the
government -- not available to a student team. This flow is built with the
identical shape (send OTP -> verify OTP -> issue session) so the mock can
be swapped for a real integration later without touching any other route.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.utils.security import hash_aadhaar, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/aadhaar/send-otp")
def send_otp(payload: schemas.AadhaarOTPRequest):
    """
    In production this would call UIDAI's OTP-generation API and text the
    real OTP to the phone linked to that Aadhaar number. Here it just
    confirms the number is well-formed and tells the frontend an OTP was
    "sent" -- the demo OTP is fixed (see MOCK_AADHAAR_OTP) so your pitch
    doesn't depend on SMS delivery working live in front of judges.
    """
    if not payload.aadhaar_number.isdigit():
        raise HTTPException(status_code=400, detail="Aadhaar number must be 12 digits")
    return {
        "message": "OTP sent to registered mobile number",
        "demo_note": f"Hackathon demo OTP is always {settings.MOCK_AADHAAR_OTP}",
    }


@router.post("/aadhaar/verify-otp", response_model=schemas.TokenResponse)
def verify_otp(payload: schemas.AadhaarOTPVerify, db: Session = Depends(get_db)):
    if payload.otp != settings.MOCK_AADHAAR_OTP:
        raise HTTPException(status_code=401, detail="Incorrect OTP")

    aadhaar_hash = hash_aadhaar(payload.aadhaar_number)
    user = db.query(models.User).filter(models.User.aadhaar_hash == aadhaar_hash).first()
    is_new_user = user is None

    if is_new_user:
        user = models.User(
            aadhaar_hash=aadhaar_hash,
            aadhaar_last4=payload.aadhaar_number[-4:],
            full_name=payload.full_name,
            preferred_language=payload.preferred_language,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Create an empty profile shell so /profile GET never 404s for a fresh user
        db.add(models.Profile(user_id=user.id, state="Andhra Pradesh"))
        db.commit()
    else:
        user.is_verified = True
        user.preferred_language = payload.preferred_language
        db.commit()

    token = create_access_token(user.id)
    return schemas.TokenResponse(access_token=token, user_id=user.id, is_new_user=is_new_user)
