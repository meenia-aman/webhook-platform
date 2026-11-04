import hashlib
import hmac
import secrets

from src.core.config import settings


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    pepper = settings.REFRESH_TOKEN_PEPPER.get_secret_value()
    token = hmac.new(
        pepper.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()

    return token


def verify_refresh_token(
    token: str,
    stored_hash: str,
) -> bool:
    calculated_hash = hash_refresh_token(token)

    return hmac.compare_digest(calculated_hash, stored_hash)
