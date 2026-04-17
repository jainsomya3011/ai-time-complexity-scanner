import re

CODE_PATTERNS = [

    # python imports
    r"\bimport\s+\w+",
    r"\bfrom\s+\w+\s+import",

    # functions
    r"\bdef\s+\w+\(",
    r"\bfunction\s+\w+\(",

    # classes
    r"\bclass\s+\w+",

    # loops
    r"\bfor\s+",
    r"\bwhile\s+",

    # conditions
    r"\bif\s+",
    r"\belse\b",

    # return
    r"\breturn\b",

    # python prints
    r"\bprint\s*\(",

    # assignments
    r"\w+\s*=\s*\w+",

    # brackets for many languages
    r"\{|\}",

    # semicolon languages
    r";",

    # C/C++ includes
    r"#include"
]


def validate_code_input(code):

    if len(code.strip()) == 0:
        raise ValueError("Empty input.")

    for pattern in CODE_PATTERNS:
        if re.search(pattern, code):
            return True

    raise ValueError(
        "Out-of-scope input detected. Please provide programming code."
    )