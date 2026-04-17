USER_ROLES = {
    "admin": ["analyze"],
    "developer": ["analyze"],
    "guest": []
}

def check_permissions(role):

    if role not in USER_ROLES:
        raise PermissionError("Invalid role")

    if "analyze" not in USER_ROLES[role]:
        raise PermissionError(
            "User not allowed to run analysis."
        )