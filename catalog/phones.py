import re

PHONE_RE = re.compile(r"^[6-9]\d{9}$")


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_phone(value: str) -> str:
    """Return a 10-digit Indian mobile number, or an empty string if invalid."""
    digits = digits_only(value)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if PHONE_RE.fullmatch(digits):
        return digits
    return ""


def format_phone(value: str) -> str:
    phone = normalize_phone(value) or digits_only(value)
    if len(phone) == 10:
        return f"{phone[:5]} {phone[5:]}"
    return value or ""
