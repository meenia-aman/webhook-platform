import email
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field


def validate_passsword(password: str):

    if password != password.strip():
        raise ValueError("Leading or trailing whitespace is not allowed")

    if not any(ch.isupper() for ch in password):
        raise ValueError("Password must contain one uppercase letter")

    if not any(ch.islower() for ch in password):
        raise ValueError("Password must contain one lowercase letter")

    if not any(ch.isdigit() for ch in password):
        raise ValueError("Password must contain one digit")

    if not any(not ch.isalnum() for ch in password):
        raise ValueError("Password must contain one special character")

    return password


Password = Annotated[
    str, Field(min_length=8, max_length=128), AfterValidator(validate_passsword)
]


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: Password


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    newPassword: Password


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordReqeust(BaseModel):
    token: str
    new_password: Password


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationEmail(BaseModel):
    email: EmailStr
