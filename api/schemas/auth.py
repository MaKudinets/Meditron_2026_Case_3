from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


UserRole = Literal[
    "patient",
    "doctor",
]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    role: UserRole


class UserResponse(BaseModel):
    id: str

    email: EmailStr

    role: UserRole

    is_email_verified: bool


class RegisterResponse(BaseModel):
    user: UserResponse

    message: str

    email_sent: bool = True


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    token: str = Field(
        ...,
        min_length=20,
        max_length=512,
    )


class ResendVerificationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


class LoginResponse(BaseModel):
    access_token: str

    token_type: Literal["bearer"] = "bearer"

    expires_at: datetime

    user: UserResponse

class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    token: str = Field(
        ...,
        min_length=20,
        max_length=512,
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )