from typing import Protocol
from uuid import UUID

from src.module.identity.models.password_reset_token_model import PasswordResetToken


class ResetPasswordRepository(Protocol):
    async def add(self, data: PasswordResetToken) -> PasswordResetToken: ...

    async def get_by_token(self, token_hash: str) -> PasswordResetToken | None: ...

    async def get_by_id(self, id: UUID) -> PasswordResetToken | None: ...
