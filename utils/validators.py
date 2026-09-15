import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value):
    return bool(value) and bool(EMAIL_RE.match(value.strip()))


def clean_text(value, max_length=2000):
    if value is None:
        return ""
    return value.strip()[:max_length]
