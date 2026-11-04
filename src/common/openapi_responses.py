from typing import Any

from src.common.responses import ErrorResponse

OpenApiResponse = dict[int | str, dict[str, Any]]

_ERROR_DESCRIPTIONS: dict[int, str] = {
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Resource not found",
    409: "Resource conflict",
    422: "Validation error",
    429: "Too many requests",
    500: "Internal server error",
}


def error_response(
    *codes: int,
    descriptions: dict[int, str] | None = None,
) -> OpenApiResponse:
    custom_descriptions = descriptions or {}
    responses: OpenApiResponse = {}

    for code in codes:
        description = custom_descriptions.get(code)
        if description is None:
            description = _ERROR_DESCRIPTIONS.get(code)

        if description is None:
            raise ValueError(f"No default OpenAPI description exists for staus {code}")

        responses[code] = {"model": ErrorResponse, "description": description}

    return responses
