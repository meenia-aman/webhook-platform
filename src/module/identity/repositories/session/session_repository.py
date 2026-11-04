from typing import Protocol
from uuid import UUID
from src.module.identity.models.auth_session_model import AuthSession


class SessionRepository(Protocol):
    async def add(
        self,
        data: AuthSession,
    ) -> AuthSession: ...

    async def get_by_id(
        self,
        session_id: UUID,
    ) -> AuthSession | None: ...

    async def get_active_session_by_userid(
        self, user_id: UUID
    ) -> list[AuthSession]: ...

    async def get_expired_session_by_userid(
        self, user_id: UUID
    ) -> list[AuthSession]: ...
