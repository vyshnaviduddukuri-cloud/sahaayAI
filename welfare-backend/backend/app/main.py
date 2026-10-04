import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

from app.database import Base, engine
from app.config import settings
from app.routers import auth, profile, eligibility, chat, documents, applications, notifications

# Creates welfare.db and all tables on first run -- zero manual setup.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend for the welfare scheme eligibility agent — Aadhaar-style verification, "
                 "multilingual profile intake, eligibility checks, document checklists, "
                 "application status tracking, and scheme notifications.",
    version="1.0.0",
)

# Wide-open CORS for hackathon dev speed. Tighten allow_origins before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(eligibility.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(applications.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health")
def health():
    return {"status": "healthy"}
