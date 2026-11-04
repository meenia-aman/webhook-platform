from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from fastapi import Request
from sqlalchemy import schema

from src.common.exceptions import (
    AuthorizationTokenNotFoundError,
    UserNotAuthenicatedError,
)
from src.core.logger import get_logger
from src.core.security.tokens import decode_access_token
from src.module.identity.models.user_model import UserRole


logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AuthContext:
    user_id: UUID
    session_id: UUID
    role: UserRole


auth_context: ContextVar[AuthContext | None] = ContextVar(
    "auth_context",
    default=None,
)


def get_auth_context() -> AuthContext:
    context = auth_context.get()

    if context is None:
        raise UserNotAuthenicatedError()

    return context


def set_auth_context(context: AuthContext):
    return auth_context.set(context)


async def auth_middleware(request: Request):

    auth_token = request.headers.get("Authorization")

    if auth_token is None:
        raise AuthorizationTokenNotFoundError()

    scheme, separoator, token = auth_token.partition(" ")

    if scheme != "Bearer":
        raise AuthorizationTokenNotFoundError()

    decoded_jwt = decode_access_token(token)

    context = AuthContext(
        user_id=decoded_jwt.sub,
        session_id=decoded_jwt.sid,
        role=decoded_jwt.role,
    )

    logger.debug(context)

    set_auth_context(context)
