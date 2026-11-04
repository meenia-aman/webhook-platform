from typing import Protocol
from uuid import UUID

from src.module.identity.models.user_model import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, data: User) -> User: ...
