from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str
    data: DataT | None = None
    meta: dict[str, Any] | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    status_code: int
    success: bool = False
    message: str
    errors: list[ErrorDetail] | None = None
