import re

SENSITIVE_REQUEST_PATTERNS = [
    "system prompt",
    "show your system prompt",
    "reveal your system prompt",
    "hidden instructions",
    "developer instructions",
    "email id",
    "email address",
    "phone number",
    "contact details",
    "api key",
    "password",
    "secret key",
]

EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"


def privacy_filter(text):

    lower = text.lower()

    for pattern in SENSITIVE_REQUEST_PATTERNS:
        if pattern in lower:
            raise ValueError(
                "Sensitive information request detected and blocked."
            )

    if re.search(EMAIL_PATTERN, text):
        raise ValueError(
            "Personal data detected (email). Request blocked."
        )