from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from src.core.security.tokens import GenerateAccessTokenResponse
from src.module.identity.dtos.session_dto import SessionResponse
from src.module.identity.models.user_model import UserRole, UserStatus


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    status: UserStatus
    created_at: datetime
    role: UserRole


class Login_Session_Status(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acceess_token: GenerateAccessTokenResponse
    user: UserResponse
    session_id: UUID
    session_status: Login_Session_Status


class LoginResponseWithActiveSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    session_id: UUID
    active_sessions: list[SessionResponse]
    session_status: Login_Session_Status


class LoginResponseWithRefreshToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    refresh_token: str
    login_response: LoginResponse | LoginResponseWithActiveSession
