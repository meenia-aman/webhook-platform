from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.common.responses import ErrorResponse
from src.core.config import settings
from src.core.exception_handlers import register_exception_handlers
from src.core.logger import get_logger, setup_logging
from src.core.middleware import add_middleware
from src.infrastructure.database.session import engine
from src.router import api_router

from fastapi.openapi.utils import get_openapi

setup_logging(level="DEBUG")

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.APP_ENV)
    yield
    # Return pooled connections to the database cleanly on shutdown.
    await engine.dispose()
    logger.info("Shutting down")


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    responses={
        "default": {"model": ErrorResponse, "description": "Unexpected error response"}
    },
)


add_middleware(app)
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health/live")
def health_check():
    return {
        "success": "True",
        "message": f"{settings.APP_NAME}, working fine",
    }


def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "SwaggerLogin"
    ] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/auth/swagger-token",
                "scopes": {},
            }
        },
    }

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
