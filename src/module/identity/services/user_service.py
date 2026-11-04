from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import (
    AccountBlockedError,
    AccountDeletedError,
    AccountNotVerifiedError,
    AccountSuspenedError,
    AppError,
    InvalidCredentialsError,
    InvalidResetPasswordToken,
    InvalidVerficationToken,
    NotFoundError,
    PasswordNotMatchError,
    UserAlreadyExistsError,
)
from src.core.config import settings
from src.core.logger import get_logger
from src.core.middleware.auth_middleware import get_auth_context
from src.core.security.opaque_tokens import generate_opaque_token_with_hash, hash_token
from src.core.security.passwords import get_password_hash, verify_password
from src.core.security.refresh_token import generate_refresh_token, hash_refresh_token
from src.core.security.tokens import generate_access_token
from src.module.identity.dtos.user_dto import (
    Login_Session_Status,
    LoginResponseWithActiveSession,
    LoginResponseWithRefreshToken,
    LoginResponse,
    UserResponse,
)
from src.module.identity.models.auth_session_model import SessionStatus
from src.module.identity.models.email_verification_token_model import (
    EmailVerificationToken,
)
from src.module.identity.models.password_reset_token_model import PasswordResetToken
from src.module.identity.models.user_model import User, UserStatus
from src.module.identity.repositories.email_verification.email_verificaion_repository import (
    EmailVerificationRepository,
)
from src.module.identity.repositories.reset_password.reset_password_repository import (
    ResetPasswordRepository,
)
from src.module.identity.repositories.users.user_repository import UserRepository
from src.module.identity.schemas.user_schema import (
    ChangePasswordRequest,
    CreateUserRequest,
    ForgotPasswordRequest,
    LoginUserRequest,
    ResendVerificationEmail,
    ResetPasswordReqeust,
    VerifyEmailRequest,
)
from src.module.identity.services.session_service import SessionService


logger = get_logger(__name__)


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        session_service: SessionService,
        reset_password_repo: ResetPasswordRepository,
        email_verificaiton_repo: EmailVerificationRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.session_service = session_service
        self.reset_password_repo = reset_password_repo
        self.email_verificaiton_repo = email_verificaiton_repo

    async def register(self, data: CreateUserRequest) -> UserResponse | None:
        logger.debug(data)

        # Check user already exits or not
        user = await self.user_repo.get_by_email(data.email)

        if user is not None:
            raise UserAlreadyExistsError()

        password_hash = get_password_hash(data.password)

        user = User(name=data.name, email=data.email, password_hash=password_hash)

        user = await self.user_repo.add(user)

        await self.session.commit()

        resendVerificationEmail = ResendVerificationEmail(email=user.email)
        await self.send_verification_email(resendVerificationEmail)

        return UserResponse.model_validate(user)

    async def login(
        self,
        data: LoginUserRequest,
        *,
        user_agent: str | None = None,
        device_name: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponseWithRefreshToken:

        user = await self.user_repo.get_by_email(data.email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError()

        # TODO: In future add the proper case for 'DELTED' user , for now we are not handling that
        if user.status == "PENDING":
            raise AccountNotVerifiedError()
        elif user.status == "SUSPENDED":
            raise AccountSuspenedError()
        elif user.status == "BLOCKED":
            raise AccountBlockedError()
        elif user.status == "DELETED":
            raise AccountDeletedError()

        refresh_token = generate_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token)

        now = datetime.now(UTC)

        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        ## Check Active session count , if active session count is greater than 5 create a pending
        ## session and return the list of all active sesion, so user can select the session which
        ## user want to revoke

        active_sessions = await self.session_service.get_active_session_by_userId(
            user.id
        )
        session_status = SessionStatus.ACTIVE

        active_sessions_len = len(active_sessions)

        if active_sessions_len >= 5:
            session_status = SessionStatus.PENDING

        session = await self.session_service.create_session(
            user_id=user.id,
            status=session_status,
            refresh_token_hash=refresh_token_hash,
            refresh_token_expiry=expires_at,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        access_token = generate_access_token(
            user_id=user.id, role=user.role, session_id=session.sessionId
        )

        login_response = (
            LoginResponse(
                acceess_token=access_token,
                user=UserResponse.model_validate(user),
                session_id=session.sessionId,
                session_status=Login_Session_Status.ACTIVE,
            )
            if active_sessions_len < 5
            else LoginResponseWithActiveSession(
                user=UserResponse.model_validate(user),
                session_id=session.sessionId,
                active_sessions=active_sessions,
                session_status=Login_Session_Status.PENDING,
            )
        )

        response = LoginResponseWithRefreshToken(
            refresh_token=refresh_token,
            login_response=login_response,
        )

        return response

    async def complete_login(
        self, session_id: UUID, prev_session_id: UUID
    ) -> LoginResponseWithRefreshToken:

        result = await self.session_service.active_pending_session(
            session_id, prev_session_id
        )

        user = await self.user_repo.get_by_id(result.user_id)

        if user is None:
            raise NotFoundError("No active sesion found")

        accessToken = generate_access_token(
            user_id=result.user_id,
            session_id=session_id,
            role=user.role,
        )

        login_response = LoginResponse(
            acceess_token=accessToken,
            user=UserResponse.model_validate(user),
            session_id=session_id,
            session_status=Login_Session_Status.ACTIVE,
        )

        response = LoginResponseWithRefreshToken(
            refresh_token=result.refresh_token,
            login_response=login_response,
        )

        return response

    async def logout(self):
        auth_context = get_auth_context()

        session = await self.session_service.get_session_by_id(auth_context.session_id)

        if session is None or session.status != "ACTIVE":
            raise NotFoundError("No active session found for user")

        now = datetime.now(UTC)
        session.status = SessionStatus.REVOKED
        session.revoke_reason = "User logout"
        session.revoked_at = now

        await self.session.commit()

        return None

    async def change_password(self, data: ChangePasswordRequest):

        auth_context = get_auth_context()

        user = await self.user_repo.get_by_id(auth_context.user_id)

        if user is None:
            raise NotFoundError()

        if verify_password(data.password, user.password_hash) is False:
            raise PasswordNotMatchError()

        password_hash = get_password_hash(data.newPassword)

        user.password_hash = password_hash

        await self.session.commit()

    async def forgot_password(self, data: ForgotPasswordRequest):

        user = await self.user_repo.get_by_email(data.email)

        if user is None:
            return

        token = generate_opaque_token_with_hash(128)

        minutes_to_add = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        expires_at = datetime.now(UTC) + timedelta(minutes=minutes_to_add)

        reset_password = PasswordResetToken(
            user_id=user.id, token_hash=token.hash, expires_at=expires_at
        )

        reset_password = await self.reset_password_repo.add(reset_password)

        # TODO: Send the acutal email to the uesr for ResetPassword

        logger.debug(f"ForgotPassword Token {token.raw}")

        await self.session.commit()

    async def reset_password(self, data: ResetPasswordReqeust):

        token_hash = hash_token(data.token)

        result = await self.reset_password_repo.get_by_token(token_hash)

        now = datetime.now(UTC)
        if result is None or result.expires_at <= now or result.revoked_at is not None:
            raise InvalidResetPasswordToken()

        user = await self.user_repo.get_by_id(result.user_id)

        if user is None:
            raise InvalidResetPasswordToken()

        password_hash = get_password_hash(data.new_password)

        user.password_hash = password_hash

        result.used_at = now
        result.revoked_at = now

        await self.session.commit()

    async def send_verification_email(self, data: ResendVerificationEmail):

        user = await self.user_repo.get_by_email(data.email)

        if user is None:
            return

        if user.status != "PENDING":
            raise AppError("Account already verified")

        token = generate_opaque_token_with_hash(128)

        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        )

        email_verification_token = EmailVerificationToken(
            user_id=user.id, token_hash=token.hash, expires_at=expires_at
        )

        await self.email_verificaiton_repo.add(email_verification_token)

        # TODO: Send the actual verificaiton eamil to user

        logger.debug(f"EmailVerificationToken : {token.raw}")

        await self.session.commit()

    async def verify_email(self, data: VerifyEmailRequest):

        token_hash = hash_token(data.token)

        result = await self.email_verificaiton_repo.get_by_token_hash(token_hash)

        now = datetime.now(UTC)

        if result is None or result.expires_at <= now or result.revoked_at is not None:
            raise InvalidVerficationToken()

        user = await self.user_repo.get_by_id(result.user_id)

        if user is None:
            raise InvalidVerficationToken()

        if user.status == "ACTIVE":
            raise AppError("Account already verified")

        result.expires_at = now
        result.revoked_at = now

        user.status = UserStatus.ACTIVE

        await self.session.commit()

        return None

    async def get_current_user_detail(self) -> UserResponse:

        auth_context = get_auth_context()

        user = await self.user_repo.get_by_id(auth_context.user_id)

        if user is None:
            raise NotFoundError("No user found")

        return UserResponse.model_validate(user)
