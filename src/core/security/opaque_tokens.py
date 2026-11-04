import hashlib
import hmac
import secrets
from typing import NamedTuple

from src.core.config import settings


class TokenPair(NamedTuple):
    raw: str
    hash: str


PEPPER = settings.OPAQUE_TOKEN_PEPPER


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    return hmac.new(
        PEPPER.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_opaque_token_with_hash(nbytes: int = 32) -> TokenPair:
    raw = generate_token(nbytes)
    hash = hash_token(raw)
    return TokenPair(raw=raw, hash=hash)


def verify_opaque_token(token: str, stored_hash: str) -> bool:
    calculated_hash = hash_token(token)
    return hmac.compare_digest(calculated_hash, stored_hash)
