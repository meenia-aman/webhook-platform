from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pydantic import BaseModel

from src.common.exceptions import InvalidTokenError
from src.core.config import settings
from src.module.identity.models.user_model import UserRole

ALGORITHM = "HS256"


class AccessTokenClaims(BaseModel):
    sub: UUID
    sid: UUID
    jti: UUID

    iss: str
    aud: str

    iat: datetime
    nbf: datetime
    exp: datetime

    token_type: str
    role: UserRole


class GenerateAccessTokenResponse(BaseModel):
    token: str
    expires_at: datetime


def generate_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    role: UserRole,
) -> GenerateAccessTokenResponse:

    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "token_type": "access",
        "role": role.value,
    }

    token = jwt.encode(
        payload,
        settings.JWT_ACCESS_SECRET.get_secret_value(),
        algorithm=ALGORITHM,
        headers={
            "typ": "JWT",
            "kid": "access-v1",
        },
    )

    return GenerateAccessTokenResponse(
        token=token,
        expires_at=expires_at,
    )


def decode_access_token(token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET.get_secret_value(),
            algorithms=[ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={
                "require": [
                    "sub",
                    "sid",
                    "jti",
                    "iss",
                    "aud",
                    "iat",
                    "nbf",
                    "exp",
                    "token_type",
                    "role",
                ]
            },
        )

        claims = AccessTokenClaims.model_validate(payload)

        if claims.token_type != "access":
            raise InvalidTokenError("Access token is not valid")

        return claims
    except Exception as exc:
        raise InvalidTokenError("Invalid or expired access token") from exc
