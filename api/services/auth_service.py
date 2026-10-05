import os

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import (
    AuthSession,
    EmailVerificationToken,
    PasswordResetToken,
    PatientProfile,
    User,
)

from api.security.passwords import (
    hash_password,
    verify_password,
)

from api.security.tokens import (
    generate_token,
    hash_token,
)


# ============================================================
# SETTINGS
# ============================================================

EMAIL_VERIFICATION_TTL_HOURS = 24

SESSION_TTL_HOURS = int(
    os.getenv(
        "SESSION_TTL_HOURS",
        "168",
    )
)
PASSWORD_RESET_TTL_MINUTES = int(
    os.getenv(
        "PASSWORD_RESET_TTL_MINUTES",
        "30",
    )
)

# ============================================================
# EXCEPTIONS
# ============================================================

class InvalidCredentialsError(ValueError):
    pass


class EmailNotVerifiedError(ValueError):
    pass


class InvalidSessionError(ValueError):
    pass
class InvalidPasswordResetTokenError(
    ValueError
):
    pass

# ============================================================
# HELPERS
# ============================================================

def is_datetime_expired(
    value: datetime,
) -> bool:
    """
    SQLite может вернуть datetime без timezone,
    поэтому обрабатываем оба варианта.
    """

    if value.tzinfo is None:
        return value <= datetime.utcnow()

    return value <= datetime.now(
        timezone.utc
    )


def normalize_email(
    email: str,
) -> str:
    return email.strip().lower()


# ============================================================
# USERS
# ============================================================

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    normalized_email = normalize_email(
        email
    )

    statement = select(
        User
    ).where(
        User.email == normalized_email
    )

    return db.scalar(
        statement
    )


# ============================================================
# EMAIL VERIFICATION
# ============================================================

def create_email_verification_token(
    db: Session,
    user: User,
) -> str:
    """
    Создаёт одноразовый token подтверждения email.

    В БД сохраняется только hash токена.
    """

    raw_token = generate_token()

    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(
            raw_token
        ),
        expires_at=(
            datetime.now(
                timezone.utc
            )
            + timedelta(
                hours=EMAIL_VERIFICATION_TTL_HOURS
            )
        ),
    )

    db.add(token)

    return raw_token


def verify_email(
    db: Session,
    *,
    raw_token: str,
) -> User:

    token_hash = hash_token(
        raw_token
    )

    statement = select(
        EmailVerificationToken
    ).where(
        EmailVerificationToken.token_hash
        == token_hash
    )

    verification = db.scalar(
        statement
    )

    if verification is None:
        raise ValueError(
            "Invalid verification token"
        )

    user = db.get(
        User,
        verification.user_id,
    )

    if user is None:
        raise ValueError(
            "User not found"
        )

    # Если токен уже использован, но email уже
    # подтверждён — повторный переход считаем успешным.
    if verification.used_at is not None:

        if user.is_email_verified:
            return user

        raise ValueError(
            "Verification token has already been used"
        )

    if is_datetime_expired(
        verification.expires_at
    ):
        raise ValueError(
            "Verification token has expired"
        )

    user.is_email_verified = True

    verification.used_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(user)

    return user


def resend_email_verification(
    db: Session,
    *,
    email: str,
) -> tuple[User | None, str | None]:

    user = get_user_by_email(
        db,
        email,
    )

    # Не раскрываем наличие email в системе.
    if user is None:
        return None, None

    if user.is_email_verified:
        return None, None

    # Все старые неиспользованные токены
    # делаем недействительными.
    statement = select(
        EmailVerificationToken
    ).where(
        EmailVerificationToken.user_id
        == user.id,
        EmailVerificationToken.used_at.is_(
            None
        ),
    )

    tokens = db.scalars(
        statement
    ).all()

    now = datetime.now(
        timezone.utc
    )

    for token in tokens:
        token.used_at = now

    raw_token = (
        create_email_verification_token(
            db,
            user,
        )
    )

    db.commit()

    return user, raw_token


# ============================================================
# REGISTRATION
# ============================================================

def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: str,
) -> tuple[User, str]:

    email = normalize_email(
        email
    )

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise ValueError(
            "User with this email already exists"
        )

    if role not in {
        "patient",
        "doctor",
    }:
        raise ValueError(
            "Unsupported user role"
        )

    user = User(
        email=email,
        password_hash=hash_password(
            password
        ),
        role=role,
        is_email_verified=False,
    )

    db.add(user)

    # Получаем user.id до commit.
    db.flush()

    # Пациент получает собственный профиль.
    # Врачу профиль пациента не нужен.
    if role == "patient":

        patient_profile = PatientProfile(
            user_id=user.id,
        )

        db.add(
            patient_profile
        )

    verification_token = (
        create_email_verification_token(
            db,
            user,
        )
    )

    db.commit()
    db.refresh(user)

    return (
        user,
        verification_token,
    )


# ============================================================
# AUTH SESSIONS
# ============================================================

def create_session(
    db: Session,
    user: User,
) -> tuple[str, AuthSession]:
    """
    Создаёт серверную сессию.

    Клиент получает raw token.
    В БД сохраняется только hash.
    """

    raw_token = generate_token()

    now = datetime.now(
        timezone.utc
    )

    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(
            raw_token
        ),
        created_at=now,
        expires_at=(
            now
            + timedelta(
                hours=SESSION_TTL_HOURS
            )
        ),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return (
        raw_token,
        session,
    )


def login_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> tuple[
    User,
    str,
    AuthSession,
]:

    user = get_user_by_email(
        db,
        email,
    )

    # Одинаковый ответ и для неизвестного email,
    # и для неправильного пароля.
    if user is None:
        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    if not user.is_email_verified:
        raise EmailNotVerifiedError(
            "Email verification is required"
        )

    raw_token, session = (
        create_session(
            db,
            user,
        )
    )

    return (
        user,
        raw_token,
        session,
    )


def get_user_session(
    db: Session,
    *,
    raw_token: str,
) -> tuple[
    User,
    AuthSession,
]:

    token_hash = hash_token(
        raw_token
    )

    statement = select(
        AuthSession
    ).where(
        AuthSession.token_hash
        == token_hash
    )

    session = db.scalar(
        statement
    )

    if session is None:
        raise InvalidSessionError(
            "Invalid session"
        )

    if session.revoked_at is not None:
        raise InvalidSessionError(
            "Session has been revoked"
        )

    if is_datetime_expired(
        session.expires_at
    ):

        session.revoked_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()

        raise InvalidSessionError(
            "Session has expired"
        )

    user = db.get(
        User,
        session.user_id,
    )

    if user is None:
        raise InvalidSessionError(
            "User not found"
        )

    return (
        user,
        session,
    )


def revoke_session(
    db: Session,
    session: AuthSession,
) -> None:
    """
    Делает session token недействительным.
    Используется при logout.
    """

    if session.revoked_at is None:

        session.revoked_at = (
            datetime.now(
                timezone.utc
            )
        )

        db.commit()


# ============================================================
# PASSWORD RESET
# ============================================================


def create_password_reset_token(
    db: Session,
    *,
    user: User,
) -> str:
    """
    Создаёт одноразовый токен восстановления пароля.

    В БД хранится только SHA-256 hash.
    Исходный токен возвращается только для отправки
    пользователю по email.
    """

    raw_token = generate_token()

    token_hash = hash_token(
        raw_token
    )

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                PASSWORD_RESET_TTL_MINUTES
            )
        )
    )

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        created_at=now,
        expires_at=expires_at,
        used_at=None,
    )

    db.add(
        reset_token
    )

    return raw_token


def request_password_reset(
    db: Session,
    *,
    email: str,
) -> tuple[
    User | None,
    str | None,
]:
    """
    Создаёт reset token, если пользователь существует.

    Для несуществующего email возвращает (None, None),
    но route всё равно должен вернуть обычный 200 OK.
    Это защищает от перебора зарегистрированных email.
    """

    normalized_email = normalize_email(
        email
    )

    user = get_user_by_email(
        db,
        normalized_email,
    )

    if user is None:
        return (
            None,
            None,
        )

    now = datetime.now(
        timezone.utc
    )

    # Старые неиспользованные reset-токены
    # для этого пользователя делаем недействительными.
    old_tokens = db.scalars(
        select(
            PasswordResetToken
        ).where(
            PasswordResetToken.user_id
            == user.id,

            PasswordResetToken.used_at
            .is_(None),
        )
    ).all()

    for old_token in old_tokens:
        old_token.used_at = now

    raw_token = (
        create_password_reset_token(
            db,
            user=user,
        )
    )

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return (
        user,
        raw_token,
    )


def reset_password(
    db: Session,
    *,
    raw_token: str,
    new_password: str,
) -> User:
    """
    Проверяет reset token и устанавливает новый пароль.

    После успешной смены:
    - reset token становится использованным;
    - все старые login sessions пользователя отзываются.
    """

    token_hash = hash_token(
        raw_token
    )

    reset_token = db.scalar(
        select(
            PasswordResetToken
        ).where(
            PasswordResetToken.token_hash
            == token_hash
        )
    )

    if reset_token is None:
        raise InvalidPasswordResetTokenError(
            "Invalid or expired password reset token"
        )

    if reset_token.used_at is not None:
        raise InvalidPasswordResetTokenError(
            "Invalid or expired password reset token"
        )

    if is_datetime_expired(
        reset_token.expires_at
    ):
        raise InvalidPasswordResetTokenError(
            "Invalid or expired password reset token"
        )

    user = db.get(
        User,
        reset_token.user_id,
    )

    if user is None:
        raise InvalidPasswordResetTokenError(
            "Invalid or expired password reset token"
        )

    now = datetime.now(
        timezone.utc
    )

    # ========================================================
    # NEW PASSWORD
    # ========================================================

    user.password_hash = hash_password(
        new_password
    )

    # Токен нельзя будет использовать повторно.
    reset_token.used_at = now

    # ========================================================
    # REVOKE OLD SESSIONS
    # ========================================================

    sessions = db.scalars(
        select(
            AuthSession
        ).where(
            AuthSession.user_id
            == user.id,

            AuthSession.revoked_at
            .is_(None),
        )
    ).all()

    for session in sessions:
        session.revoked_at = now

    try:
        db.commit()

        db.refresh(
            user
        )

    except Exception:
        db.rollback()
        raise

    return user