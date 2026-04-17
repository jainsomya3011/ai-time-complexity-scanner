import json
from datetime import datetime

def log_security_event(event, reason):

    log = {
        "time": str(datetime.utcnow()),
        "event": event,
        "reason": reason
    }

    with open("security_logs.json", "a") as f:
        json.dump(log, f)
        f.write("\n")