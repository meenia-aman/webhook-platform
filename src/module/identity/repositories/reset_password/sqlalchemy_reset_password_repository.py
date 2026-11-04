from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.module.identity.models.password_reset_token_model import PasswordResetToken
from src.module.identity.repositories.reset_password.reset_password_repository import (
    ResetPasswordRepository,
)


class SqlAchemyResetPasswordRepository(ResetPasswordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, data: PasswordResetToken) -> PasswordResetToken:
        self.session.add(data)
        await self.session.flush()
        return data

    async def get_by_id(self, id: UUID) -> PasswordResetToken | None:
        return await self.session.get(PasswordResetToken, id)

    async def get_by_token(self, token_hash: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()
