from src.core.correlation import new_correlation_id, correlation_id_ctx
from fastapi import Request, Response


async def add_correlation_id(request: Request, call_next):

    correlation_id = new_correlation_id()
    token = correlation_id_ctx.set(correlation_id)

    try:
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    finally:
        correlation_id_ctx.reset(token)
