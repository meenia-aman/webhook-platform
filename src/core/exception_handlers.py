from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.common.exceptions import AppError
from src.common.responses import ErrorDetail, ErrorResponse
from src.core.logger import get_logger

logger = get_logger(__name__)

REQUEST_LOCATION_PREFIXES = {
    "body",
    "query",
    "path",
    "header",
    "cookie",
}


# ValidationError handling, Error due to pydantic for incoming Request
async def request_validation_hanlder(
    request: Request,
    exc: Exception,
) -> JSONResponse:

    assert isinstance(exc, RequestValidationError)
    errors: list[ErrorDetail] = []

    for error in exc.errors():
        location = list(error.get("loc", ()))

        if location and location[0] in REQUEST_LOCATION_PREFIXES:
            location = location[1:]

        errors.append(
            ErrorDetail(
                field=".".join(str(part) for part in location) or None,
                message=error.get(
                    "msg",
                    "Invalid value",
                ),
            )
        )

    body = ErrorResponse(
        status_code=422,
        message="Request validation failed",
        errors=errors,
    )

    return JSONResponse(
        status_code=422,
        content=body.model_dump(
            mode="json",
            exclude_none=True,
        ),
    )


# AppError hanlde custom Error handle
async def app_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:

    assert isinstance(exc, AppError)

    logger.info(
        "Application error: method=%s path=%s status=%s message=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.message,
    )

    body = ErrorResponse(
        message=exc.message,
        errors=exc.errors,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(mode="json"),
    )


async def validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, ValidationError)

    errors = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]) or None,
            message=error["msg"],
        )
        for error in exc.errors()
    ]

    body = ErrorResponse(
        status_code=500,
        message="Response validation failed",
        errors=errors,
    )

    return JSONResponse(
        status_code=500,
        content=body.model_dump(mode="json", exclude_none=True),
    )


# Global Error Handler for handling any unhanlded exception
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
):

    logger.error(
        "Unhandled exception: method=%s path=%s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    body = ErrorResponse(
        status_code=500,
        success=False,
        message="Internal server error ",
    )

    return JSONResponse(
        status_code=500,
        content=body.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_hanlder)
    app.add_exception_handler(ValidationError, validation_error)
    app.add_exception_handler(Exception, unexpected_error_handler)
