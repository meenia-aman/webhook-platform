from datetime import UTC, datetime
from operator import and_, or_
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


from src.module.identity.models.auth_session_model import AuthSession, SessionStatus
from src.module.identity.repositories.session.session_repository import (
    SessionRepository,
)


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def add(
        self,
        data: AuthSession,
    ) -> AuthSession:
        self.session.add(data)
        print("Data ", data.user_id)
        await self.session.flush()
        return data

    async def get_by_id(
        self,
        session_id: UUID,
    ) -> AuthSession | None:
        return await self.session.get(AuthSession, session_id)

    async def get_active_session_by_userid(
        self,
        user_id: UUID,
    ) -> List[AuthSession]:
        statement = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.status == SessionStatus.ACTIVE,
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_expired_session_by_userid(
        self,
        user_id: UUID,
    ) -> list[AuthSession]:
        now = datetime.now(UTC)

        statement = select(AuthSession).where(
            AuthSession.user_id == user_id,
            or_(
                and_(
                    AuthSession.expires_at <= now,
                    AuthSession.status.in_(
                        [SessionStatus.PENDING, SessionStatus.ACTIVE]
                    ),
                ),
                and_(
                    AuthSession.revoked_at <= now,
                    AuthSession.status == SessionStatus.ACTIVE,
                ),
            ),
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())
