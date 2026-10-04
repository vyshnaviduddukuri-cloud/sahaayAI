"""
Scheme database with machine-readable eligibility rules.

Each rule key maps to a profile field. Supported rule shapes:
  {"min": X}              -> profile[field] >= X
  {"max": X}               -> profile[field] <= X
  {"in": [...]}             -> profile[field] in [...]
  {"eq": X}                 -> profile[field] == X

A scheme is ELIGIBLE if every rule passes.
A scheme is NEARLY_ELIGIBLE if exactly one rule fails, and that failure is
"close" (within a tolerance for numeric rules) -- this is what powers the
"almost eligible" feature.
Otherwise it's left out of both lists entirely (not shown) to keep the UI
focused -- showing 20 flatly "ineligible" schemes helps no one.

`submission_location` is a short code (not free text) pointing into
LOCATION_LABELS below, so the same scheme can describe where to apply in
English, Telugu, or Hindi without duplicating the office name everywhere.
"""

SCHEMES = [
    {
        "scheme_id": "pm_kisan",
        "name": "PM-KISAN",
        "benefit": "₹6,000/year (in 3 installments)",
        "rules": {
            "occupation": {"in": ["farmer"]},
            "land_holding_acres": {"max": 5},
        },
        "documents": ["Aadhaar card", "Land ownership papers", "Bank passbook"],
        "apply_url": "https://pmkisan.gov.in",
        "submission_location": "secretariat",
        "description": "Income support for small and marginal farmer families across India.",
    },
    {
        "scheme_id": "nsap_widow",
        "name": "NSAP — Indira Gandhi National Widow Pension",
        "benefit": "₹500-2500/month (varies by state top-up)",
        "rules": {
            "marital_status": {"in": ["widow", "widower"]},
            "age": {"min": 40, "max": 79},
            "ration_card": {"in": ["BPL"]},
        },
        "documents": ["Aadhaar card", "Death certificate of spouse", "BPL ration card", "Bank passbook"],
        "apply_url": "https://nsap.nic.in",
        "submission_location": "secretariat",
        "description": "Monthly pension for widows from below-poverty-line households.",
    },
    {
        "scheme_id": "nsap_old_age",
        "name": "NSAP — Indira Gandhi National Old Age Pension",
        "benefit": "₹200-1000/month (varies by state top-up)",
        "rules": {
            "age": {"min": 60},
            "ration_card": {"in": ["BPL"]},
        },
        "documents": ["Aadhaar card", "Age proof", "BPL ration card"],
        "apply_url": "https://nsap.nic.in",
        "submission_location": "secretariat",
        "description": "Monthly pension for senior citizens from below-poverty-line households.",
    },
    {
        "scheme_id": "nsap_disability",
        "name": "NSAP — Indira Gandhi National Disability Pension",
        "benefit": "₹300-1500/month (varies by state top-up)",
        "rules": {
            "age": {"min": 18, "max": 79},
            "disability_pct": {"min": 80},
            "ration_card": {"in": ["BPL"]},
        },
        "documents": ["Aadhaar card", "Disability certificate (80%+)", "BPL ration card"],
        "apply_url": "https://nsap.nic.in",
        "submission_location": "secretariat",
        "description": "Monthly pension for persons with severe disabilities from BPL households.",
    },
    {
        "scheme_id": "pmay_g",
        "name": "PMAY-G (Pradhan Mantri Awaas Yojana — Gramin)",
        "benefit": "₹1.2-1.3 lakh housing assistance",
        "rules": {
            "annual_income": {"max": 300000},
            "ration_card": {"in": ["BPL"]},
        },
        "documents": ["Aadhaar card", "BPL ration card", "Land/site ownership proof"],
        "apply_url": "https://pmayg.nic.in",
        "submission_location": "secretariat",
        "description": "Financial assistance to build a pucca house for eligible rural households.",
    },
    {
        "scheme_id": "ap_scholarship",
        "name": "AP State Post-Matric Scholarship",
        "benefit": "Full tuition fee reimbursement",
        "rules": {
            "is_student": {"eq": True},
            "age": {"max": 25},
            "annual_income": {"max": 250000},
            "state": {"in": ["Andhra Pradesh"]},
        },
        "documents": ["Aadhaar card", "Income certificate", "Caste certificate (if applicable)", "Bonafide student certificate"],
        "apply_url": "https://jnanabhumi.ap.gov.in",
        "submission_location": "mandal_office",
        "description": "Tuition fee support for students from low-income families in Andhra Pradesh.",
    },
    {
        "scheme_id": "ayushman_bharat",
        "name": "Ayushman Bharat PM-JAY",
        "benefit": "₹5 lakh/year health cover",
        "rules": {
            "ration_card": {"in": ["BPL"]},
            "annual_income": {"max": 250000},
        },
        "documents": ["Aadhaar card", "BPL ration card", "Family ID"],
        "apply_url": "https://pmjay.gov.in",
        "submission_location": "secretariat",
        "description": "Free health insurance cover up to ₹5 lakh per family per year.",
    },
    {
        "scheme_id": "sukanya_samriddhi",
        "name": "Sukanya Samriddhi Yojana",
        "benefit": "High-interest savings for girl child",
        "rules": {
            "gender": {"in": ["female"]},
            "age": {"max": 10},
        },
        "documents": ["Aadhaar card", "Girl child's birth certificate"],
        "apply_url": "https://www.nsiindia.gov.in",
        "submission_location": "bank",
        "description": "Savings scheme for the welfare of a girl child, opened before she turns 10.",
    },
    {
        "scheme_id": "ujjwala",
        "name": "Pradhan Mantri Ujjwala Yojana",
        "benefit": "Free LPG connection",
        "rules": {
            "ration_card": {"in": ["BPL"]},
            "gender": {"in": ["female"]},
        },
        "documents": ["Aadhaar card", "BPL ration card", "Bank passbook"],
        "apply_url": "https://pmuy.gov.in",
        "submission_location": "secretariat",
        "description": "Free LPG gas connection for women from below-poverty-line households.",
    },
    {
        "scheme_id": "disability_pension_ap",
        "name": "AP State Disability Pension",
        "benefit": "₹3,000/month",
        "rules": {
            "disability_pct": {"min": 40},
            "state": {"in": ["Andhra Pradesh"]},
        },
        "documents": ["Aadhaar card", "Disability certificate (40%+)"],
        "apply_url": "https://ap.gov.in",
        "submission_location": "secretariat",
        "description": "State-level monthly pension for persons with 40% or higher disability.",
    },
]

# Numeric tolerance used for "nearly eligible" -- e.g. income within this
# much of the limit, or age within this many years, counts as "close".
NEARLY_TOLERANCE = {
    "annual_income": 30000,
    "age": 3,
    "land_holding_acres": 0.5,
    "disability_pct": 10,
}

# Where each submission_location code points, per language. Keep the
# wording concrete and local ("Sachivalayam") rather than generic
# ("government office") -- that specificity is the whole point of this
# feature for elderly/low-literacy users.
LOCATION_LABELS = {
    "secretariat": {
        "en": "your Village/Ward Secretariat (Sachivalayam) — ask for the Welfare Assistant",
        "te": "మీ గ్రామ/వార్డు సచివాలయం — సంక్షేమ సహాయకుడిని అడగండి",
        "hi": "अपने ग्राम/वार्ड सचिवालय — कल्याण सहायक से मिलें",
    },
    "mandal_office": {
        "en": "your Mandal Revenue Office (MRO office)",
        "te": "మీ మండల రెవెన్యూ కార్యాలయం (MRO కార్యాలయం)",
        "hi": "अपने मंडल राजस्व कार्यालय (MRO कार्यालय)",
    },
    "bank": {
        "en": "the bank branch where you hold your account",
        "te": "మీ ఖాతా ఉన్న బ్యాంకు శాఖ",
        "hi": "वह बैंक शाखा जहाँ आपका खाता है",
    },
}