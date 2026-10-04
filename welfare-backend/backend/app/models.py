import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    """
    One row per verified citizen. aadhaar_number is stored HASHED, never
    plaintext -- see utils/security.py. This table is only ever written to
    after successful (mock) OTP verification.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    aadhaar_hash = Column(String, unique=True, index=True, nullable=False)
    aadhaar_last4 = Column(String(4), nullable=False)  # display only, e.g. "XXXX-XXXX-1234"
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    preferred_language = Column(String, default="te")  # ISO code: te, hi, en, ...
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    eligibility_results = relationship("EligibilityResult", back_populates="user")


class Profile(Base):
    """
    The structured welfare-eligibility profile -- matches the AI service's
    input contract exactly. One-to-one with User.
    """
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    state = Column(String, default="Andhra Pradesh")
    district = Column(String, nullable=True)
    annual_income = Column(Float, nullable=True)
    category = Column(String, nullable=True)          # SC/ST/OBC/General
    occupation = Column(String, nullable=True)
    land_holding_acres = Column(Float, nullable=True)
    ration_card = Column(String, nullable=True)        # BPL/APL/None
    disability_pct = Column(Integer, default=0)
    marital_status = Column(String, nullable=True)
    is_student = Column(Boolean, default=False)
    raw_intake_text = Column(Text, nullable=True)      # original free-text the user spoke/typed
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

    def to_ai_payload(self) -> dict:
        """Shape this profile exactly as the AI service's /check and /extract expect."""
        return {
            "age": self.age,
            "gender": self.gender,
            "state": self.state,
            "district": self.district,
            "annual_income": self.annual_income,
            "category": self.category,
            "occupation": self.occupation,
            "land_holding_acres": self.land_holding_acres,
            "ration_card": self.ration_card,
            "disability_pct": self.disability_pct,
            "marital_status": self.marital_status,
            "is_student": self.is_student,
        }


class EligibilityResult(Base):
    """
    Cached snapshot of the AI service's last /check response for a user, so
    the document checklist and dashboard don't have to re-call the AI
    service on every page load.
    """
    __tablename__ = "eligibility_results"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    eligible = Column(JSON, default=list)          # list[dict] -- scheme_id, name, reasons, documents...
    nearly_eligible = Column(JSON, default=list)
    ineligible = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="eligibility_results")


class Application(Base):
    """
    A scheme the user has (or says they have) applied for. Powers the
    status-checking feature. Status is updated either by the user manually
    ("I submitted it on this date") or, if you later wire a real portal
    integration/scraper, by a background job.
    """
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    scheme_id = Column(String, nullable=False)
    scheme_name = Column(String, nullable=False)
    reference_number = Column(String, nullable=True)   # acknowledgment number from the govt portal, if any
    status = Column(String, default="draft")            # draft -> submitted -> under_review -> approved/rejected
    submitted_office = Column(String, nullable=True)     # where they said they'd submit / did submit
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")


class Notification(Base):
    """
    Scheme-specific notifications (PM-KISAN installment releases, deadline
    reminders, etc). Populated by a periodic job hitting NotificationSource
    -- see routers/notifications.py for the hackathon-appropriate approach.
    """
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # null = broadcast to all
    scheme_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
