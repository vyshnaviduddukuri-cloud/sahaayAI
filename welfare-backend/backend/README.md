# Welfare Scheme Eligibility — Backend

FastAPI backend implementing: Aadhaar-style verified login, multilingual
profile intake (form + voice/text), eligibility checking (proxied to your
teammate's AI service), document checklists, application status tracking,
and scheme notifications (PM-KISAN and others).

## 1. Setup (one-time)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then edit JWT_SECRET before your demo
```

## 2. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` — FastAPI auto-generates a full
interactive API tester (Swagger UI). Use this to demo the backend alone,
independent of the frontend, if anything goes wrong live.

The SQLite database file (`welfare.db`) is created automatically on first
run. Delete it any time to reset all demo data.

## 3. How this connects to the other two repos

```
React frontend  ──HTTP/JSON──▶  THIS BACKEND (port 8000)  ──HTTP/JSON──▶  AI service (port 8001)
                                        │
                                   welfare.db (SQLite)
```

- **Frontend** calls only this backend. Never calls the AI service directly.
- **AI service** (your teammate) must expose exactly three endpoints this
  backend calls: `POST /extract`, `POST /check`, `POST /chat`. See
  `app/config.py` → `AI_SERVICE_URL` to point at wherever they run it.
- If the AI service is down or not built yet, every route that depends on
  it fails with a clean `503`, not a crash — the rest of the app (auth,
  profile, notifications, applications) works standalone. This was tested
  above.

## 4. Environment variables (`.env`)

| Variable | Purpose | Demo default |
|---|---|---|
| `JWT_SECRET` | Signs session tokens | **change before your demo** |
| `DATABASE_URL` | DB connection string | `sqlite:///./welfare.db` |
| `MOCK_AADHAAR_OTP` | Fixed OTP for the mock verification flow | `123456` |
| `AI_SERVICE_URL` | Base URL of your teammate's AI service | `http://localhost:8001` |

## 5. API reference

All routes except `/auth/*` and `/health` require
`Authorization: Bearer <token>`, obtained from `/auth/aadhaar/verify-otp`.

### Auth (mock Aadhaar — see note below)
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/aadhaar/send-otp` | Validates Aadhaar number format, "sends" OTP |
| POST | `/auth/aadhaar/verify-otp` | Verifies OTP, creates/logs in user, returns JWT |

### Profile
| Method | Path | Purpose |
|---|---|---|
| GET | `/profile` | Fetch the logged-in user's profile |
| PUT | `/profile` | Update profile fields directly (manual form) |
| POST | `/profile/intake` | Free-text/voice-transcribed input → AI-extracted profile |

### Eligibility
| Method | Path | Purpose |
|---|---|---|
| POST | `/eligibility/check` | Runs profile through the AI rules engine, caches result |
| GET | `/eligibility/latest` | Reads the last cached result without re-checking |

### Chat
| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Grounded Q&A, proxied to the AI service's RAG agent |

### Documents
| Method | Path | Purpose |
|---|---|---|
| GET | `/documents/checklist` | Deduplicated document list across all eligible schemes |

### Applications (status tracking)
| Method | Path | Purpose |
|---|---|---|
| POST | `/applications` | Mark a scheme as applied for |
| GET | `/applications` | List all applications + their status |
| PATCH | `/applications/{id}/status` | Update status (draft/submitted/under_review/approved/rejected) |

### Notifications (PM-KISAN etc.)
| Method | Path | Purpose |
|---|---|---|
| GET | `/notifications` | List notifications relevant to the user (auto-seeds demo data) |
| POST | `/notifications/{id}/read` | Mark a notification as read |

## 6. Important honesty notes for your pitch / Q&A

Be upfront about these two if judges ask — it reads as engineering maturity,
not a weakness:

- **Aadhaar verification is mocked.** Real UIDAI integration requires
  government AUA/KUA empanelment, not available to a student team. The
  flow (`send-otp` → `verify-otp` → session token) is built identically to
  the real one, so swapping in a real integration later only touches
  `app/routers/auth.py` — nothing else in the app changes.
- **Application status tracking is self-reported, not a live government
  portal scrape.** PM-KISAN and most state portals don't expose a public
  status API. Users (or you, in the demo) update status manually. A real
  v2 would need official API access or a permitted scraping agreement.

## 7. Build order if you're finishing this yourself

1. ✅ Auth, profile, notifications, applications — done, tested, working standalone.
2. Point `AI_SERVICE_URL` at your teammate's running service once `/extract`,
   `/check`, `/chat` exist — test `/eligibility/check` and `/chat` end-to-end.
3. Wire the frontend to these exact routes (see API reference above) —
   share this README with your frontend teammate directly.
4. Before the demo: reset `welfare.db`, run through the full flow once
   (send-otp → verify-otp → update profile → check eligibility → chat →
   checklist → applications → notifications) to catch anything broken.
