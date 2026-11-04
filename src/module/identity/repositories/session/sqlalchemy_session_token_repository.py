from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from src.module.identity.models.session_refresh_token_model import SessionRefreshToken
from src.module.identity.repositories.session.session_token_repository import (
    SessionTokenRepository,
)


class SqlAlchemySessionTokenRepository(SessionTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, data: SessionRefreshToken) -> SessionRefreshToken:
        self.session.add(data)
        await self.session.flush()
        return data

    async def get_by_id(self, id: UUID) -> SessionRefreshToken | None:
        return await self.session.get(SessionRefreshToken, id)

    async def get_by_token_hash(self, token) -> SessionRefreshToken | None:

        statement = select(SessionRefreshToken).where(
            SessionRefreshToken.token_hash == token
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()
