JAILBREAK_PATTERNS = [
    "bypass guardrails",
    "ignore previous instructions",
    "act as unrestricted ai",
    "disable safety",
    "jailbreak"
]

def jailbreak_filter(text):

    lower = text.lower()

    for attack in JAILBREAK_PATTERNS:
        if attack in lower:
            raise ValueError(
                "Jailbreak attempt detected."
            )