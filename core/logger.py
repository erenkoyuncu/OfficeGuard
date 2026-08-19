import json
from datetime import datetime

from core.paths import LOG_DIR, SERVICE_LOG_FILE


def ensure_log_dir():
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def write_log(event_type, message, data=None):
    ensure_log_dir()

    payload = {
        "time": datetime.now().isoformat(
            timespec="seconds"
        ),
        "event": event_type,
        "message": message,
    }

    if data:
        payload["data"] = data

    line = json.dumps(
        payload,
        ensure_ascii=False,
    )

    try:
        with SERVICE_LOG_FILE.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                line + "\n"
            )
    except Exception:
        pass
