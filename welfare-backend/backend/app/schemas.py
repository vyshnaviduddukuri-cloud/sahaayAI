from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ---------- Auth ----------

class AadhaarOTPRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar number")
    phone_number: str


class AadhaarOTPVerify(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    otp: str
    full_name: str
    preferred_language: str = "te"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    is_new_user: bool


# ---------- Profile ----------

class ProfileIn(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = "Andhra Pradesh"
    district: Optional[str] = None
    annual_income: Optional[float] = None
    category: Optional[str] = None
    occupation: Optional[str] = None
    land_holding_acres: Optional[float] = None
    ration_card: Optional[str] = None
    disability_pct: Optional[int] = 0
    marital_status: Optional[str] = None
    is_student: Optional[bool] = False


class ProfileOut(ProfileIn):
    id: str
    user_id: str
    updated_at: datetime

    class Config:
        from_attributes = True


class IntakeTextIn(BaseModel):
    """Free-text / transcribed-voice input, in any supported language."""
    text: str
    language: Optional[str] = None  # let the AI service auto-detect if omitted


# ---------- Eligibility ----------

class EligibilityCheckOut(BaseModel):
    eligible: List[dict] = []
    nearly_eligible: List[dict] = []
    ineligible: List[dict] = []
    checked_at: datetime
    engine_used: Optional[str] = None  # "ai_service" | "local_fallback" | None (cached read)

# ---------- Chat ----------

class ChatIn(BaseModel):
    message: str
    language: Optional[str] = None


class ChatOut(BaseModel):
    reply: str
    sources: List[str] = []


# ---------- Documents ----------

class DocumentChecklistOut(BaseModel):
    documents: List[str]
    per_scheme: dict


# ---------- Applications ----------

class ApplicationIn(BaseModel):
    scheme_id: str
    scheme_name: str
    reference_number: Optional[str] = None
    submitted_office: Optional[str] = None
    notes: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: str  # draft | submitted | under_review | approved | rejected
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: str
    scheme_id: str
    scheme_name: str
    reference_number: Optional[str]
    status: str
    submitted_office: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Notifications ----------

class NotificationOut(BaseModel):
    id: str
    scheme_id: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
