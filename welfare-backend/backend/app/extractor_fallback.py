"""
Local fallback for free-text profile extraction. Used when the AI
service's /extract endpoint is unreachable, so "Tell us about yourself"
still works end-to-end during a demo.

This is deliberately simple keyword/pattern matching, not an LLM -- it
won't be as flexible as a real extractor, but it reliably catches the
common phrasings in English, Hindi (romanized + Devanagari), and Telugu
for the fields the rules engine actually needs.
"""
import re

MARITAL_KEYWORDS = {
    "widow": ["widow", "vidhwa", "విధవ", "భర్త చనిపోయ"],
    "widower": ["widower"],
    "married": ["married", "shadi", "వివాహ"],
    "single": ["single", "unmarried", "పెళ్లి కాలేదు"],
}

GENDER_KEYWORDS = {
    "female": ["female", "woman", "mahila", "స్త్రీ", "మహిళ", "ఆమె", "she "],
    "male": ["male", "man", "purush", "పురుషుడు", "అతను", "he "],
}

OCCUPATION_KEYWORDS = {
    "farmer": ["farmer", "farming", "kisan", "raithu", "రైతు", "వ్యవసాయ"],
    "none": ["no job", "unemployed", "no income", "housewife", "గృహిణి"],
}

RATION_CARD_KEYWORDS = {
    "BPL": ["bpl", "below poverty", "పేదరిక రేఖకు దిగువ"],
    "APL": ["apl", "above poverty"],
}


def _find_number_near(text: str, keywords: list[str]) -> float | None:
    """Finds a number that appears close to any of the given keywords."""
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue
        window = text[max(0, idx - 20): idx + 40]
        match = re.search(r"\d+(?:\.\d+)?", window)
        if match:
            return float(match.group())
    return None


def _match_keyword_dict(text: str, keyword_dict: dict) -> str | None:
    text_lower = text.lower()
    for value, keywords in keyword_dict.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return value
    return None


def extract_profile(text: str) -> dict:
    """Returns a partial profile dict -- only fields it's confident about.
    Missing fields are simply omitted (None), same as the AI service
    contract, so the caller merges this the same way either path."""
    result = {}

    # Age: look for a 1-2 digit number followed by "year(s)", "yrs", "ఏళ్ళు", or standalone "I'm NN"
    age_match = re.search(r"\b(\d{1,3})\s*(?:years?|yrs?|ఏళ్ళు|ఏళ్లు)\b", text, re.IGNORECASE)
    if not age_match:
        age_match = re.search(r"\bi'?m\s+(\d{1,3})\b", text, re.IGNORECASE)
    if age_match:
        age = int(age_match.group(1))
        if 1 <= age <= 120:
            result["age"] = age

    result["marital_status"] = _match_keyword_dict(text, MARITAL_KEYWORDS)
    result["gender"] = _match_keyword_dict(text, GENDER_KEYWORDS)
    result["occupation"] = _match_keyword_dict(text, OCCUPATION_KEYWORDS)
    result["ration_card"] = _match_keyword_dict(text, RATION_CARD_KEYWORDS)

    # Widow/widower implies gender if not already caught
    if not result.get("gender"):
        if result.get("marital_status") == "widow":
            result["gender"] = "female"
        elif result.get("marital_status") == "widower":
            result["gender"] = "male"

    income = _find_number_near(text, ["income", "earn", "₹", "rs.", "rs ", "salary"])
    if income is not None:
        result["annual_income"] = income

    land = _find_number_near(text, ["acre", "acres", "ఎకరం", "ఎకరాల"])
    if land is not None:
        result["land_holding_acres"] = land

    if re.search(r"\bstudent\b|విద్యార్థి", text, re.IGNORECASE):
        result["is_student"] = True

    # Drop keys where nothing matched, so we never overwrite a saved
    # profile field with None
    return {k: v for k, v in result.items() if v is not None}