import time
import uuid
from fastapi import Request

from app.logging import log_event
from app.request_context import request_id_ctx


async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    token = request_id_ctx.set(request_id)

    start = time.perf_counter()

    log_event(
        "request_start",
        method=request.method,
        path=request.url.path,
    )

    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - start) * 1000

        log_event(
            "request_end",
            duration_ms=round(duration_ms, 2),
            status_code=getattr(response, "status_code", None),
        )

        request_id_ctx.reset(token)

