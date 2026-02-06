import json
import logging
from pathlib import Path
from app.request_context import request_id_ctx

_LOGGER_NAME = "chronicle"


def setup_logging(level: str, log_file: str) -> None:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(getattr(handler, "baseFilename", "")) == log_path:
                return

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_event(event: str, **kwargs) -> None:
    payload = {
        "event": event,
        "request_id": request_id_ctx.get(),
        **kwargs,
    }
    logging.getLogger(_LOGGER_NAME).info(json.dumps(payload))
