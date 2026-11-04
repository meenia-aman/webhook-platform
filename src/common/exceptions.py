from src.common.responses import ErrorDetail


class AppError(Exception):
    status_code: int = 400
    success: bool = False
    message: str = "An error occurred"
    errors: list[ErrorDetail] | None = None

    def __init__(
        self, message: str | None = None, *, errors: list[ErrorDetail] | None = None
    ) -> None:
        if message is not None:
            self.message = message

        self.errors = errors

        super().__init__(self.message)


class NotFoundError(AppError):
    status_code: int = 404
    message: str = "Resource not found"


class InternalServerError(AppError):
    status_code: int = 500
    message: str = "Internal server error"


class UserAlreadyExistsError(AppError):
    status_code: int = 400
    message: str = "User with this email already exists. please try to login"


class InvalidCredentialsError(AppError):
    status_code: int = 400
    message: str = "Invalid credentials"


class InvalidTokenError(AppError):
    message: str = "Token is not valid"


class InvalidRefreshTokenError(AppError):
    message: str = "Refersh token is invalid or expired"


class NoRefreshTokenFoundError(AppError):
    message: str = "No refresh token found"


class AccountNotVerifiedError(AppError):
    message: str = "Account not verified, please verify you account to login"


class AccountSuspenedError(AppError):
    message: str = (
        "Your account is suspended, please contact the team to resolve this issue"
    )


class AccountBlockedError(AppError):
    message: str = (
        "Your account is blocked, please contact the team to resolve this issue"
    )


class AccountDeletedError(AppError):
    message: str = "Your account is deleted"


class UserNotAuthenicatedError(AppError):
    message: str = "User must be authenticated "


class AuthorizationTokenNotFoundError(AppError):
    message: str = "Authorization token is missing"


class PasswordNotMatchError(AppError):
    message: str = "Invalid current password"


class InvalidResetPasswordToken(AppError):
    message: str = "Invalid or Expired reset password token"


class InvalidVerficationToken(AppError):
    message: str = "Invalid or Expired Verification Token"
