from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.cookies import cookie_config
from src.common.exceptions import NoRefreshTokenFoundError
from src.core.config import settings

from src.common.openapi_responses import error_response
from src.common.responses import ApiResponse
from src.core.logger import get_logger
from src.core.middleware.auth_middleware import auth_middleware
from src.infrastructure.database.session import get_db
from src.module.identity.dtos.session_dto import SessionResponse
from src.module.identity.dtos.user_dto import (
    Login_Session_Status,
    LoginResponse,
    LoginResponseWithActiveSession,
    UserResponse,
)
from src.module.identity.repositories.email_verification.email_verificaion_repository import (
    EmailVerificationRepository,
)
from src.module.identity.repositories.email_verification.sqlalchemy_email_verificaion_repository import (
    SqlAlchemyEmailVerificationRepository,
)
from src.module.identity.repositories.reset_password.reset_password_repository import (
    ResetPasswordRepository,
)
from src.module.identity.repositories.reset_password.sqlalchemy_reset_password_repository import (
    SqlAchemyResetPasswordRepository,
)
from src.module.identity.repositories.session.session_repository import (
    SessionRepository,
)
from src.module.identity.repositories.session.session_token_repository import (
    SessionTokenRepository,
)
from src.module.identity.repositories.session.sqlalchemy_session_respository import (
    SqlAlchemySessionRepository,
)
from src.module.identity.repositories.session.sqlalchemy_session_token_repository import (
    SqlAlchemySessionTokenRepository,
)
from src.module.identity.repositories.users.sqlalchemy_user_respository import (
    SQLAlchemyUserRepository,
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
from src.module.identity.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

logger = get_logger(__name__)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_sesssion_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionRepository:
    return SqlAlchemySessionRepository(session)


def get_session_token_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionTokenRepository:
    return SqlAlchemySessionTokenRepository(session)


def get_reset_password_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResetPasswordRepository:
    return SqlAchemyResetPasswordRepository(session)


def get_email_verification_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> EmailVerificationRepository:

    return SqlAlchemyEmailVerificationRepository(session)


def get_session_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    session_repo: Annotated[SessionRepository, Depends(get_sesssion_repository)],
    session_token_repo: Annotated[
        SessionTokenRepository, Depends(get_session_token_repository)
    ],
) -> SessionService:
    return SessionService(
        session,
        session_repo,
        session_token_repo,
    )


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    reset_password_repo: Annotated[
        ResetPasswordRepository, Depends(get_reset_password_repository)
    ],
    email_verification_repo: Annotated[
        EmailVerificationRepository, Depends(get_email_verification_repository)
    ],
):
    return UserService(
        session,
        user_repo,
        session_service,
        reset_password_repo,
        email_verification_repo,
    )


@router.post("/register", response_model=ApiResponse[UserResponse])
async def create_user(
    data: CreateUserRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
    response: Response,
):
    print(data)
    result = await user_service.register(data)

    response_data = ApiResponse(
        message="User create successfully",
        data=result,
    )
    print(request.headers.get("user-agent"))
    return response_data


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse | LoginResponseWithActiveSession],
    responses=error_response(400),
)
async def login(
    request: Request,
    response: Response,
    data: LoginUserRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("device-name")
    ip_address = request.client.host if request.client else None

    result = await user_service.login(
        data, user_agent=user_agent, device_name=device_name, ip_address=ip_address
    )

    response_data = ApiResponse(
        message="Login successfully", data=result.login_response
    )

    if result.login_response.session_status == Login_Session_Status.ACTIVE:
        response.set_cookie(value=result.refresh_token, **cookie_config.options)

    return response_data


@router.post(
    "/refresh-session",
    response_model=ApiResponse,
)
async def referesh_session(
    session_service: Annotated[SessionService, Depends(get_session_service)],
    request: Request,
    response: Response,
):

    token = request.cookies.get(settings.REFRESH_TOKEN_KEY)

    if token is None:
        raise NoRefreshTokenFoundError()

    result = await session_service.refresh_session(token)

    response_data = ApiResponse(message=f"Session refresh successfully {result}")

    response.set_cookie(value=result, **cookie_config.options)

    return response_data


@router.get(
    "/session/{user_id}",
    response_model=ApiResponse[list[SessionResponse]],
)
async def get_sessions(
    user_id: UUID,
    session_service: Annotated[SessionService, Depends(get_session_service)],
):

    result = await session_service.get_active_session_by_userId(user_id)

    return ApiResponse(message="Sessions fetched successfully", data=result)


@router.post("/login/complete", response_model=ApiResponse[LoginResponse])
async def complete_login(
    response: Response,
    session_id: UUID,
    revoked_session_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    result = await user_service.complete_login(session_id, revoked_session_id)

    response.set_cookie(value=result.refresh_token, **cookie_config.options)

    response_data = ApiResponse(
        message="Login successfully", data=result.login_response
    )

    return response_data


@router.get("/session/revoke/{session_id}", response_model=ApiResponse)
async def revoke_session(
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(get_session_service)],
):

    await session_service.revoke_session(session_id)

    return ApiResponse(
        message="Session revoked successfully",
    )


@router.post("/session/revoke", response_model=ApiResponse)
async def revoke_sessions(
    user_id: Annotated[UUID, Body(embed=True)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
):

    await session_service.revoke_sessions(user_id)

    return ApiResponse(message="All sessions revoked successfully")


@router.get(
    "/logout",
    response_model=ApiResponse,
    dependencies=[Depends(auth_middleware)],
    openapi_extra={"security": [{"SwaggerLogin": []}]},
)
async def logout(
    request: Request, user_service: Annotated[UserService, Depends(get_user_service)]
):
    await user_service.logout()

    response = ApiResponse(message="User logout successfully")
    return response


@router.post(
    "/swagger-token",
    include_in_schema=False,
)
async def swagger_token(
    form: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    auth_service: Annotated[UserService, Depends(get_user_service)],
):

    data = LoginUserRequest(email=form.username, password=form.password)
    result = await auth_service.login(data)

    if not isinstance(result.login_response, LoginResponse):
        raise HTTPException(
            status_code=409,
            detail="Session limit exhausted, so can't create new session",
        )

    token = result.login_response.acceess_token.token

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.post(
    "/change-password",
    dependencies=[Depends(auth_middleware)],
    response_model=ApiResponse,
    openapi_extra={"security": [{"SwaggerLogin": []}]},
)
async def change_password(
    data: ChangePasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    await user_service.change_password(data)

    response = ApiResponse(message="Password changes successfully")

    return response


@router.post("/forgot-password", response_model=ApiResponse)
async def frogot_password(
    data: ForgotPasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    await user_service.forgot_password(data)

    response = ApiResponse(
        message="If your account exists, we have send the email to reset you password"
    )

    return response


@router.post("/reset-password", response_model=ApiResponse)
async def reset_password(
    data: ResetPasswordReqeust,
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    await user_service.reset_password(data)
    response = ApiResponse(message="Password changes successfully")

    return response


@router.post("/verification/resend", response_model=ApiResponse)
async def resend_verification_email(
    data: ResendVerificationEmail,
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    await user_service.send_verification_email(data)

    response = ApiResponse(
        message="New verification email has sent to your registered email"
    )

    return response


@router.post("/verify", response_model=ApiResponse)
async def verify_account(
    data: VerifyEmailRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    await user_service.verify_email(data)

    resposne = ApiResponse(
        message="Account verified successfully.You can now login to access the platform"
    )

    return resposne


@router.get(
    "/me",
    dependencies=[Depends(auth_middleware)],
    response_model=ApiResponse[UserResponse],
    openapi_extra={"security": [{"SwaggerLogin": []}]},
)
async def get_current_user_detail(
    user_service: Annotated[UserService, Depends(get_user_service)],
):

    result = await user_service.get_current_user_detail()

    response = ApiResponse(
        message="User detailed fetched successfully",
        data=result,
    )

    return response
