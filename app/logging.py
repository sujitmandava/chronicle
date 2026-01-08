import logging
import json
import sys
from app.request_context import request_id_ctx


def setup_logging(level: str):
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )


def log_event(event: str, **kwargs):
    payload = {
        "event": event,
        "request_id": request_id_ctx.get(),
        **kwargs,
    }
    logging.info(json.dumps(payload))
