from dataclasses import dataclass

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import (
    AuthSession,
    User,
)
from api.services.auth_service import (
    InvalidSessionError,
    get_user_session,
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


@dataclass
class AuthContext:
    user: User
    session: AuthSession


def unauthorized_exception():
    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail="Authentication required",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def get_current_auth(
    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(bearer_scheme),

    db: Session = Depends(get_db),
) -> AuthContext:

    if credentials is None:
        raise unauthorized_exception()

    if (
        credentials.scheme.lower()
        != "bearer"
    ):
        raise unauthorized_exception()

    try:
        user, session = get_user_session(
            db,
            raw_token=(
                credentials.credentials
            ),
        )

    except InvalidSessionError:
        raise unauthorized_exception()

    return AuthContext(
        user=user,
        session=session,
    )


def get_current_user(
    auth: AuthContext = Depends(
        get_current_auth
    ),
) -> User:

    return auth.user