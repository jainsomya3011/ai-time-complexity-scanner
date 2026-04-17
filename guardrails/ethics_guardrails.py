BANNED_WORDS = [
    "kill",
    "bomb",
    "weapon",
    "hack",
    "ddos",
    "malware"
]

def ethical_filter(text):

    lower = text.lower()

    for word in BANNED_WORDS:
        if word in lower:
            raise ValueError(
                "Ethical violation detected."
            )