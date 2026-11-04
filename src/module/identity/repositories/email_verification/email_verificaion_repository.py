from typing import Protocol
from uuid import UUID

from src.module.identity.models.email_verification_token_model import (
    EmailVerificationToken,
)


class EmailVerificationRepository(Protocol):
    async def add(self, data: EmailVerificationToken) -> EmailVerificationToken: ...

    async def get_by_token_hash(
        self, token_hash: str
    ) -> EmailVerificationToken | None: ...

    async def get_by_id(self, id: UUID) -> EmailVerificationToken | None: ...
