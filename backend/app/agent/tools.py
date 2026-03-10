"""
Validation and normalization logic for the two agent tools:
  - log_interaction
  - edit_interaction
"""

from datetime import date, datetime

VALID_INTERACTION_TYPES = {"Meeting", "Call", "Email", "Conference"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}


def _normalize_sentiment(value: str) -> str:
    mapping = {
        "positive": "Positive",
        "neutral": "Neutral",
        "negative": "Negative",
    }
    return mapping.get(value.strip().lower(), "Neutral")


def _normalize_interaction_type(value: str) -> str:
    mapping = {
        "meeting": "Meeting",
        "call": "Call",
        "phone call": "Call",
        "email": "Email",
        "conference": "Conference",
    }
    return mapping.get(value.strip().lower(), "Meeting")


def _normalize_date(value: str) -> str | None:
    """Try to parse common date formats and return YYYY-MM-DD."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Handle relative dates
    lower = value.strip().lower()
    if lower == "today":
        return date.today().strftime("%Y-%m-%d")
    if lower == "yesterday":
        from datetime import timedelta
        return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    return value  # return as-is if we can't parse


def _ensure_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def validate_and_normalize(fields: dict) -> dict:
    """Validate and normalize extracted fields."""
    normalized = {}

    for key, value in fields.items():
        if value is None or value == "" or value == []:
            continue

        if key == "sentiment":
            normalized[key] = _normalize_sentiment(str(value))
        elif key == "interaction_type":
            normalized[key] = _normalize_interaction_type(str(value))
        elif key == "date":
            parsed = _normalize_date(str(value))
            if parsed:
                normalized[key] = parsed
        elif key in ("attendees", "materials_shared", "samples_distributed"):
            normalized[key] = _ensure_list(value)
        elif key in (
            "hcp_name",
            "time",
            "topics_discussed",
            "outcomes",
            "follow_up_actions",
        ):
            normalized[key] = str(value).strip()
        # Ignore unknown fields

    return normalized


def log_interaction(extracted_fields: dict) -> dict:
    """
    Tool 1: log_interaction
    Validates and normalizes all extracted fields for a new interaction log.
    Returns the full set of cleaned fields.
    """
    return validate_and_normalize(extracted_fields)


def edit_interaction(extracted_fields: dict, current_form_state: dict) -> dict:
    """
    Tool 2: edit_interaction
    Validates only the changed fields and merges them with the current state.
    Returns only the changed fields (normalized).
    """
    return validate_and_normalize(extracted_fields)
