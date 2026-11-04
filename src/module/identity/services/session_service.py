from datetime import datetime, timezone, UTC
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import InvalidRefreshTokenError, NotFoundError
from src.core.logger import get_logger
from src.core.security.refresh_token import generate_refresh_token, hash_refresh_token
from src.module.identity.dtos.session_dto import (
    ActivePendingSesionResponse,
    SessionResponse,
)
from src.module.identity.models.auth_session_model import AuthSession, SessionStatus
from src.module.identity.models.session_refresh_token_model import SessionRefreshToken
from src.module.identity.repositories.session.session_repository import (
    SessionRepository,
)
from src.module.identity.repositories.session.session_token_repository import (
    SessionTokenRepository,
)

logger = get_logger(__name__)


class CreateSessionResponse(BaseModel):
    sessionId: UUID


class SessionService:
    def __init__(
        self,
        session: AsyncSession,
        session_repo: SessionRepository,
        session_token_repo: SessionTokenRepository,
    ) -> None:
        self.session = session
        self.session_repo = session_repo
        self.session_token_repo = session_token_repo

    # Create user session for login
    async def create_session(
        self,
        *,
        user_id: UUID,
        refresh_token_hash: str,
        refresh_token_expiry: datetime,
        status: SessionStatus,
        device_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> CreateSessionResponse:

        auth_session = AuthSession(
            user_id=user_id,
            expires_at=refresh_token_expiry,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            last_used_at=datetime.now(),
            status=status,
        )

        logger.debug("Auth Session")
        print(
            auth_session.user_id,
            " ip_address",
            auth_session.ip_address,
        )

        auth_session: AuthSession = await self.session_repo.add(auth_session)

        sessionRefreshToken = SessionRefreshToken(
            session_id=auth_session.id,
            token_hash=refresh_token_hash,
            expires_at=refresh_token_expiry,
        )

        sessionRefreshToken = await self.session_token_repo.add(sessionRefreshToken)

        await self.session.commit()

        return CreateSessionResponse(sessionId=auth_session.id)

    # Get Session By Id
    async def get_session_by_id(self, sessionId: UUID) -> AuthSession | None:

        return await self.session_repo.get_by_id(sessionId)

    # Mark the current refresh_token as revoked and generate a new entry and return new
    # refresh_token
    async def refresh_session(self, refresh_token: str) -> str:

        token_hash = hash_refresh_token(refresh_token)

        auth_session = await self.session_token_repo.get_by_token_hash(token_hash)

        if auth_session is None:
            raise InvalidRefreshTokenError()

        # Check the status of session whether that session is active or not
        user_session = await self.session_repo.get_by_id(auth_session.session_id)

        if user_session is None or user_session.status != "ACTIVE":
            raise InvalidRefreshTokenError()

        now = datetime.now(timezone.utc)
        if auth_session.expires_at <= now or auth_session.revoked_at is not None:
            raise InvalidRefreshTokenError()

        new_refresh_token = generate_refresh_token()
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)

        # Revoke the previous rerfresh_token of the session
        auth_session.revoked_at = datetime.now()

        new_session_token = SessionRefreshToken(
            session_id=auth_session.session_id,
            token_hash=new_refresh_token_hash,
            expires_at=auth_session.expires_at,
            replaced_by_token_id=auth_session.id,
        )

        await self.session_token_repo.add(new_session_token)

        await self.session.commit()

        return new_refresh_token

    ## Mark  All Exipred sessions as revoked to get the actual Active session count
    async def revoke_expired_session(self, user_id: UUID):

        sessions = await self.session_repo.get_expired_session_by_userid(user_id)

        for auth_session in sessions:
            auth_session.status = SessionStatus.REVOKED

        await self.session.commit()

    # Get all session by userId
    async def get_active_session_by_userId(self, userId: UUID) -> list[SessionResponse]:

        await self.revoke_expired_session(userId)

        sessions = await self.session_repo.get_active_session_by_userid(userId)

        return [
            SessionResponse.model_validate(auth_session) for auth_session in sessions
        ]

    ## Create New Session to complete the login which was on hold due to Active Session
    ## Limit and also mark the previus session as Revoked

    async def active_pending_session(
        self, session_id: UUID, previous_session_id: UUID
    ) -> ActivePendingSesionResponse:

        current_session = await self.get_session_by_id(session_id)
        previous_session = await self.get_session_by_id(previous_session_id)

        if current_session is None or previous_session is None:
            raise NotFoundError("No active session found")

        if current_session.status != "PENDING" or previous_session.status != "ACTIVE":
            raise NotFoundError("No active session found")

        current_session.status = SessionStatus.ACTIVE
        previous_session.status = SessionStatus.PENDING
        previous_session.revoked_at = datetime.now(UTC)
        previous_session.revoke_reason = "Session revoked due to new session creation"

        new_refresh_token = generate_refresh_token()
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)

        new_session_token = SessionRefreshToken(
            session_id=session_id,
            token_hash=new_refresh_token_hash,
            expires_at=current_session.expires_at,
        )

        await self.session_token_repo.add(new_session_token)

        await self.session.commit()

        return ActivePendingSesionResponse(
            user_id=current_session.user_id,
            refresh_token=new_refresh_token,
        )

    # Revoke Active Session
    async def revoke_session(self, session_id: UUID):

        # TODO: Compare the logged_id user_id with sessions user_id, they must belong to same user
        auth_session = await self.session_repo.get_by_id(session_id)

        if auth_session is None or auth_session.status != "ACTIVE":
            raise NotFoundError("No active sesion found for the provided session_id")

        now = datetime.now(UTC)

        auth_session.status = SessionStatus.REVOKED
        auth_session.revoked_at = now
        auth_session.revoke_reason = "Session revoked by user"

        await self.session.commit()

    # Revoke all session except the current session from where user is trying to revoke the session
    # TODO: Don't take userId from the user, just get it from the access token
    async def revoke_sessions(self, user_id: UUID):
        auth_sessions = await self.session_repo.get_active_session_by_userid(user_id)

        if len(auth_sessions) <= 0:
            raise NotFoundError("No session found")

        now = datetime.now(UTC)

        for auth_session in auth_sessions:
            auth_session.status = SessionStatus.REVOKED
            auth_session.revoked_at = now
            auth_session.revoke_reason = "All sessions revoked by user"

        await self.session.commit()
