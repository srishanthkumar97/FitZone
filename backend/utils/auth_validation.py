import re
from datetime import date
from urllib.parse import urlsplit


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PHONE_PATTERN = re.compile(r"^[0-9+() .-]{7,32}$")
ALLOWED_GENDERS = {"male", "female", "non-binary", "other", "prefer_not_to_say"}


def validate_email(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if len(normalized) > 255 or not EMAIL_PATTERN.fullmatch(normalized):
        return None
    return normalized


def validate_phone(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    digit_count = sum(character.isdigit() for character in normalized)
    if not PHONE_PATTERN.fullmatch(normalized) or digit_count < 7:
        return None
    return normalized


def validate_date_of_birth(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        result = date.fromisoformat(value)
    except ValueError:
        return None
    if result > date.today():
        return None
    return result


def validate_profile_photo(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if len(normalized) > 2048:
        return None
    try:
        parts = urlsplit(normalized)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return None
        parts.port
    except ValueError:
        return None
    return normalized
