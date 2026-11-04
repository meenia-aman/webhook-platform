from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, IPvAnyAddress

from src.infrastructure.database.base import Base
from src.module.identity.models.auth_session_model import SessionStatus


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: str | None
    user_agent: str | None
    ip_address: IPvAnyAddress | None
    created_at: datetime
    last_used_at: datetime
    status: SessionStatus


class ActivePendingSesionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    refresh_token: str
