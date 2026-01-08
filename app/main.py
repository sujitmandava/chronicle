from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.ui import router as ui_router
from app.logging import setup_logging
from app.config import settings
from app.middleware import request_context_middleware

setup_logging(settings.log_level, settings.log_file)

app = FastAPI(title=settings.app_name)

app.middleware("http")(request_context_middleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui_router)
app.include_router(api_router)
