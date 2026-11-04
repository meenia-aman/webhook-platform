from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.module.identity.models.email_verification_token_model import (
    EmailVerificationToken,
)
from src.module.identity.repositories.email_verification.email_verificaion_repository import (
    EmailVerificationRepository,
)


class SqlAlchemyEmailVerificationRepository(EmailVerificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, data: EmailVerificationToken) -> EmailVerificationToken:
        self.session.add(data)
        await self.session.flush()
        return data

    async def get_by_token_hash(self, token_hash: str) -> EmailVerificationToken | None:
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> EmailVerificationToken | None:
        return await self.session.get(EmailVerificationToken, id)
