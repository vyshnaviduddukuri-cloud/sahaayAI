# Sahayata — Frontend

Plain HTML/CSS/JS — no build step, no npm install. Talks directly to your
FastAPI backend.

## Run it

You can't just double-click `index.html` (the browser blocks some fetch
calls from `file://` URLs). Serve it locally instead — one line, no install:

```bash
cd frontend
python -m http.server 5500
```

Then open **http://localhost:5500** in your browser.

## Before you open it

Your backend must already be running on `http://127.0.0.1:8000` (see the
backend's own README). If you changed the backend's port, update
`API_BASE` at the very top of `js/app.js` to match.

## What's wired up

Every feature from the plan is connected to a real backend call:

| Feature | Where |
|---|---|
| Aadhaar OTP login | Login page → `/auth/aadhaar/send-otp` + `/verify-otp` |
| Manual profile form | Dashboard → `/profile` (GET/PUT) |
| Voice/text intake | Dashboard "Tell us about yourself" box → `/profile/intake`. Voice uses the browser's built-in Web Speech API (Chrome works best) to transcribe speech, then sends the text — no extra service needed. |
| Eligibility check + reasons | Dashboard → `/eligibility/check` |
| "Almost eligible" | Same response, rendered in the amber-bordered cards |
| Document checklist | Dashboard → `/documents/checklist` |
| Chat / follow-up questions | Dashboard → `/chat` |
| Application status tracking | Dashboard sidebar → `/applications` |
| PM-KISAN / scheme notifications | Notifications page → `/notifications` |

## Known limitation for the demo

The hero slider on the homepage ("Recently updated schemes") uses static
demo data in `js/app.js` (`RECENT_SCHEMES`), since the backend doesn't
expose a public "list all schemes" endpoint yet. If you add one
(`GET /schemes` returning the AI service's scheme catalog), swap that
array for a real fetch — everything else in the file already follows that
pattern.

## If something doesn't load

Open the browser console (F12 → Console tab). Every API call here throws
a readable error message on failure — if the backend isn't running, or
CORS is misconfigured, you'll see exactly which call failed and why,
rather than a silent blank screen.
