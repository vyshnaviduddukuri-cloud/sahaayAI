"""
Deterministic local eligibility engine. Zero LLM calls -- pure rule
evaluation, so results are explainable, reproducible, and never hallucinated.

This exists as a FALLBACK and safety net: the primary path is still your AI
teammate's /check endpoint (richer reasoning, RAG-grounded explanations).
But a hackathon demo cannot depend entirely on a second person's service
being up at the exact moment you're on stage -- so if that call fails, is
slow, or returns something malformed, this engine runs instead and the
demo keeps working.
"""
from app.data.schemes import SCHEMES, NEARLY_TOLERANCE, LOCATION_LABELS

WHERE_TO_APPLY_TEMPLATE = {
    "en": "To apply for {scheme}, go to: {location}. Carry these documents: {docs}. You can also check {apply_url} online.",
    "te": "{scheme} కోసం దరఖాస్తు చేయడానికి ఇక్కడికి వెళ్ళండి: {location}. వెంట తీసుకెళ్లవలసిన పత్రాలు: {docs}. ఆన్‌లైన్‌లో {apply_url} కూడా చూడవచ్చు.",
    "hi": "{scheme} के लिए आवेदन करने हेतु यहाँ जाएं: {location}. साथ ले जाने वाले दस्तावेज़: {docs}. आप ऑनलाइन {apply_url} भी देख सकते हैं.",
}


def _rule_passes(value, rule: dict) -> bool:
    if value is None:
        return False
    if "min" in rule and value < rule["min"]:
        return False
    if "max" in rule and value > rule["max"]:
        return False
    if "in" in rule and value not in rule["in"]:
        return False
    if "eq" in rule and value != rule["eq"]:
        return False
    return True


def _rule_gap_description(field: str, value, rule: dict) -> str | None:
    tolerance = NEARLY_TOLERANCE.get(field)

    if "min" in rule and (value is None or value < rule["min"]):
        if value is None:
            return None
        gap = rule["min"] - value
        if tolerance and gap <= tolerance:
            return f"{field.replace('_', ' ')} needs to be at least {rule['min']} (you're {gap:.0f} short)"
        return None

    if "max" in rule and value is not None and value > rule["max"]:
        gap = value - rule["max"]
        if tolerance and gap <= tolerance:
            return f"{field.replace('_', ' ')} must be under {rule['max']} (you're {gap:.0f} over)"
        return None

    if "in" in rule and value not in rule["in"]:
        return None

    return None


def _build_where_to_apply(scheme: dict, language: str) -> str:
    lang = language if language in WHERE_TO_APPLY_TEMPLATE else "en"
    location_code = scheme.get("submission_location", "secretariat")
    location_text = LOCATION_LABELS.get(location_code, LOCATION_LABELS["secretariat"]).get(
        lang, LOCATION_LABELS["secretariat"]["en"]
    )
    docs_text = ", ".join(scheme["documents"])
    return WHERE_TO_APPLY_TEMPLATE[lang].format(
        scheme=scheme["name"],
        location=location_text,
        docs=docs_text,
        apply_url=scheme["apply_url"],
    )


def check_eligibility(profile: dict, language: str = "en") -> dict:
    """
    profile: dict matching Profile.to_ai_payload() shape.
    language: "en" | "te" | "hi" -- controls the where_to_apply text only;
    reasons/field names stay in English for now (see note in README about
    full UI localization being a separate, larger effort).
    Returns {"eligible": [...], "nearly_eligible": [...], "ineligible": []}
    """
    eligible = []
    nearly_eligible = []

    for scheme in SCHEMES:
        rules = scheme["rules"]
        failed_fields = []

        for field, rule in rules.items():
            value = profile.get(field)
            if not _rule_passes(value, rule):
                failed_fields.append((field, value, rule))

        if not failed_fields:
            reasons = [_matched_reason(field, profile.get(field), rule) for field, rule in rules.items()]
            eligible.append({
                "scheme_id": scheme["scheme_id"],
                "name": scheme["name"],
                "benefit": scheme["benefit"],
                "reasons": reasons,
                "documents": scheme["documents"],
                "apply_url": scheme["apply_url"],
                "where_to_apply": _build_where_to_apply(scheme, language),
            })
        elif len(failed_fields) == 1:
            field, value, rule = failed_fields[0]
            gap_desc = _rule_gap_description(field, value, rule)
            if gap_desc:
                nearly_eligible.append({
                    "scheme_id": scheme["scheme_id"],
                    "name": scheme["name"],
                    "benefit": scheme["benefit"],
                    "missing": gap_desc.capitalize(),
                })

    return {"eligible": eligible, "nearly_eligible": nearly_eligible, "ineligible": []}


def _matched_reason(field: str, value, rule: dict) -> str:
    label = field.replace("_", " ")
    if "in" in rule:
        return f"{label.capitalize()}: {value}"
    if "min" in rule and "max" in rule:
        return f"{label.capitalize()} ({value}) is within the required range"
    if "min" in rule:
        return f"{label.capitalize()} ({value}) meets the minimum of {rule['min']}"
    if "max" in rule:
        return f"{label.capitalize()} ({value}) is under the limit of {rule['max']}"
    if "eq" in rule:
        return f"{label.capitalize()} matches"
    return f"{label.capitalize()} matches"