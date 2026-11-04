import time

from fastapi import Request

from src.core.logger import get_logger


logger = get_logger(__name__)


async def log_requests(request: Request, call_next):

    start_time = time.perf_counter()
    response = await call_next(request)
    response_time = time.perf_counter() - start_time

    logger.info(
        f"{request.method}  {request.url.path} {response.status_code} {response_time:.3f}s"
    )
    return response
