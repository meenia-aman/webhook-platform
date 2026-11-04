from fastapi import FastAPI

from src.core.middleware.correlation_id import add_correlation_id
from src.core.middleware.request_logging import log_requests


def add_middleware(app: FastAPI):
    app.middleware("http")(log_requests)
    app.middleware("http")(add_correlation_id)
