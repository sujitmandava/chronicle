import json
import logging
from pathlib import Path
from app.request_context import request_id_ctx


def setup_logging(level: str, log_file: str):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )


def log_event(event: str, **kwargs):
    payload = {
        "event": event,
        "request_id": request_id_ctx.get(),
        **kwargs,
    }
    logging.info(json.dumps(payload))
