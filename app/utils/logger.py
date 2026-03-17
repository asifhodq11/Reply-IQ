# ============================================================
# ReplyIQ Backend — Structured JSON Logger
# ============================================================

import json
import logging
import sys
from datetime import datetime
from flask import request, has_request_context

# Configure the root logger
logger = logging.getLogger("replyiq")
logger.setLevel(logging.INFO)

# Only add handler if not already present (prevents duplicates when reloading)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)


def log_event(event_name: str, user_id=None, level="info", **kwargs):
    """
    Logs a strictly formatted JSON event for Railway's log explorer.
    """
    event_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "event": event_name,
    }

    if user_id:
        event_data["user_id"] = str(user_id)

    # Attach any extra context data
    if kwargs:
        event_data.update(kwargs)

    # Attach request context if we are inside a Flask route
    if has_request_context():
        event_data["method"] = request.method
        event_data["path"] = request.path
        # Limit IP tracking if needed, otherwise grab remote_addr
        event_data["ip"] = request.remote_addr

    log_json = json.dumps(event_data)

    if level == "error":
        logger.error(log_json)
    elif level == "warning":
        logger.warning(log_json)
    elif level == "debug":
        logger.debug(log_json)
    else:
        logger.info(log_json)
