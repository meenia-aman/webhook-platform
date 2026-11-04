from typing import Protocol
from uuid import UUID

from src.module.identity.models.session_refresh_token_model import SessionRefreshToken


class SessionTokenRepository(Protocol):
    async def add(self, data: SessionRefreshToken) -> SessionRefreshToken: ...

    async def get_by_id(self, id: UUID) -> SessionRefreshToken | None: ...

    async def get_by_token_hash(self, token) -> SessionRefreshToken | None: ...
