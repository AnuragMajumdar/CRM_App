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


def _normalize_time(value: str) -> str | None:
    """Try to parse common time formats and return HH:MM in 24-hour format."""
    if not value:
        return None
    stripped = value.strip()
    # Already in HH:MM 24h format
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(stripped, fmt).strftime("%H:%M")
        except ValueError:
            continue
    # 12-hour formats: "2:30 PM", "2:30PM", "02:30 pm"
    for fmt in ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p"):
        try:
            return datetime.strptime(stripped, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return stripped  # return as-is if we can't parse


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
        elif key == "time":
            parsed = _normalize_time(str(value))
            if parsed:
                normalized[key] = parsed
        elif key in (
            "hcp_name",
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


def summarize_voice_interaction(extracted_fields: dict) -> dict:
    """
    Tool 3: summarize_voice_interaction
    Validates and normalizes fields extracted from a voice note transcription.
    Returns the full set of cleaned fields (same normalization as log_interaction).
    """
    return validate_and_normalize(extracted_fields)


# ---------------------------------------------------------------------------
#  Tool 4 & 5 — schedule_followup / validate_history_query
# ---------------------------------------------------------------------------

VALID_FOLLOWUP_TYPES = {"Meeting", "Call", "Email"}


def _normalize_followup_type(value: str) -> str:
    mapping = {
        "meeting": "Meeting",
        "call": "Call",
        "phone call": "Call",
        "email": "Email",
    }
    return mapping.get(value.strip().lower(), "Call")


def _normalize_relative_date(value: str) -> str | None:
    """Parse relative date expressions like 'next Tuesday', 'in 2 weeks'."""
    import re
    from datetime import timedelta

    if not value:
        return None

    # First try standard date parsing via existing helper
    parsed = _normalize_date(value)
    if parsed and parsed != value:
        return parsed

    lower = value.strip().lower()

    # "today"
    if lower == "today":
        return date.today().strftime("%Y-%m-%d")

    # "tomorrow"
    if lower == "tomorrow":
        return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # "in X days/weeks"
    match = re.match(r"in\s+(\d+)\s+(day|days|week|weeks)", lower)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if "week" in unit:
            num *= 7
        return (date.today() + timedelta(days=num)).strftime("%Y-%m-%d")

    # "X days/weeks" (without "in")
    match = re.match(r"(\d+)\s+(day|days|week|weeks)", lower)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if "week" in unit:
            num *= 7
        return (date.today() + timedelta(days=num)).strftime("%Y-%m-%d")

    # "next monday/tuesday/..."
    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    for day_name, day_num in day_names.items():
        if day_name in lower:
            today = date.today()
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # Fallback: return whatever _normalize_date gives us
    return _normalize_date(value)


def schedule_followup(extracted_fields: dict) -> dict:
    """
    Tool 4: schedule_followup
    Validates and normalizes extracted followup scheduling fields.
    Returns cleaned fields ready for DB persistence.
    """
    normalized = {}

    hcp_name = extracted_fields.get("hcp_name")
    if hcp_name and str(hcp_name).strip():
        normalized["hcp_name"] = str(hcp_name).strip()

    task = extracted_fields.get("task")
    if task and str(task).strip():
        normalized["task"] = str(task).strip()

    due_date = extracted_fields.get("due_date")
    if due_date:
        parsed = _normalize_relative_date(str(due_date))
        if parsed:
            normalized["due_date"] = parsed

    followup_type = extracted_fields.get("followup_type")
    if followup_type and str(followup_type).strip():
        normalized["followup_type"] = _normalize_followup_type(str(followup_type))
    else:
        normalized["followup_type"] = "Call"

    notes = extracted_fields.get("notes")
    if notes and str(notes).strip():
        normalized["notes"] = str(notes).strip()

    normalized["status"] = "pending"

    return normalized


def validate_history_query(extracted_fields: dict) -> dict:
    """
    Tool 5: validate_history_query
    Validates and normalizes HCP history lookup parameters.
    Returns cleaned query params.
    """
    normalized = {}

    hcp_name = extracted_fields.get("hcp_name")
    if hcp_name and str(hcp_name).strip():
        normalized["hcp_name"] = str(hcp_name).strip()

    limit = extracted_fields.get("limit")
    if limit:
        try:
            normalized["limit"] = min(int(limit), 20)
        except (ValueError, TypeError):
            normalized["limit"] = 5
    else:
        normalized["limit"] = 5

    return normalized
