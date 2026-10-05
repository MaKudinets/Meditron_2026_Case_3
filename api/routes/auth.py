import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from api.database.database import (
    get_db,
)

from api.database.models import (
    User,
)

from api.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserResponse,
    VerifyEmailRequest,
)

from api.security.auth import (
    AuthContext,
    get_current_auth,
    get_current_user,
)

from api.services.auth_service import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    login_user,
    register_user,
    request_password_reset,
    resend_email_verification,
    reset_password,
    revoke_session,
    verify_email,
)

from api.services.email_service import (
    EmailDeliveryError,
    send_password_reset_email,
    send_verification_email,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


# ============================================================
# REGISTER
# ============================================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
)
def register(
    request: RegisterRequest,

    db: Session = Depends(
        get_db
    ),
) -> RegisterResponse:

    try:

        (
            user,
            verification_token,
        ) = register_user(
            db,
            email=str(
                request.email
            ),
            password=request.password,
            role=request.role,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(
                error
            ),
        )

    email_sent = True

    try:

        send_verification_email(
            user.email,
            verification_token,
        )

    except EmailDeliveryError:

        logger.exception(
            (
                "Verification email "
                "delivery failed"
            )
        )

        email_sent = False

    return RegisterResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_email_verified=(
                user.is_email_verified
            ),
        ),

        message=(
            "Registration successful. "
            "Email verification is required."
        ),

        email_sent=email_sent,
    )


# ============================================================
# VERIFY EMAIL
# ============================================================


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
)
def verify_user_email(
    request: VerifyEmailRequest,

    db: Session = Depends(
        get_db
    ),
) -> MessageResponse:

    try:

        verify_email(
            db,
            raw_token=request.token,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )

    return MessageResponse(
        message=(
            "Email successfully verified."
        )
    )


# ============================================================
# RESEND VERIFICATION
# ============================================================


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend email verification",
)
def resend_verification(
    request: ResendVerificationRequest,

    db: Session = Depends(
        get_db
    ),
) -> MessageResponse:

    user, token = (
        resend_email_verification(
            db,
            email=str(
                request.email
            ),
        )
    )

    if (
        user is not None
        and token is not None
    ):

        try:

            send_verification_email(
                user.email,
                token,
            )

        except EmailDeliveryError:

            logger.exception(
                (
                    "Verification email "
                    "delivery failed"
                )
            )

    return MessageResponse(
        message=(
            "If the account exists and requires "
            "verification, a verification message "
            "has been sent."
        )
    )


# ============================================================
# LOGIN
# ============================================================


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login",
)
def login(
    request: LoginRequest,

    db: Session = Depends(
        get_db
    ),
) -> LoginResponse:

    try:

        (
            user,
            access_token,
            session,
        ) = login_user(
            db,
            email=str(
                request.email
            ),
            password=request.password,
        )

    except InvalidCredentialsError:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    except EmailNotVerifiedError:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Email verification is required"
            ),
        )

    return LoginResponse(
        access_token=access_token,

        expires_at=(
            session.expires_at
        ),

        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_email_verified=(
                user.is_email_verified
            ),
        ),
    )


# ============================================================
# CURRENT USER
# ============================================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
def get_me(
    user: User = Depends(
        get_current_user
    ),
) -> UserResponse:

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_email_verified=(
            user.is_email_verified
        ),
    )


# ============================================================
# LOGOUT
# ============================================================


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
)
def logout(
    auth: AuthContext = Depends(
        get_current_auth
    ),

    db: Session = Depends(
        get_db
    ),
) -> MessageResponse:

    revoke_session(
        db,
        auth.session,
    )

    return MessageResponse(
        message=(
            "Successfully logged out."
        )
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
)
def forgot_password(
    request: ForgotPasswordRequest,

    db: Session = Depends(
        get_db
    ),
) -> MessageResponse:
    """
    Ответ одинаковый и для существующего,
    и для несуществующего email.
    """

    user, token = (
        request_password_reset(
            db,
            email=str(
                request.email
            ),
        )
    )

    if (
        user is not None
        and token is not None
    ):

        try:

            send_password_reset_email(
                user.email,
                token,
            )

        except EmailDeliveryError:

            # Ошибку пишем в серверный лог,
            # но клиенту наличие аккаунта
            # не раскрываем.
            logger.exception(
                (
                    "Password reset email "
                    "delivery failed"
                )
            )

    return MessageResponse(
        message=(
            "If an account with this email exists, "
            "password reset instructions have been sent."
        )
    )


# ============================================================
# RESET PASSWORD
# ============================================================


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
)
def reset_user_password(
    request: ResetPasswordRequest,

    db: Session = Depends(
        get_db
    ),
) -> MessageResponse:

    try:

        reset_password(
            db,
            raw_token=(
                request.token
            ),
            new_password=(
                request.new_password
            ),
        )

    except InvalidPasswordResetTokenError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )

    return MessageResponse(
        message=(
            "Password successfully changed."
        )
    )