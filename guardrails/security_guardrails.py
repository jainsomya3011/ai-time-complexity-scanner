import re

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"password\s*=",
    r"api_key\s*="
]

def security_scan(code):

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, code):
            raise ValueError(
                "Sensitive information detected."
            )