import os
import smtplib

from email.message import EmailMessage
from urllib.parse import urlencode


EMAIL_MODE = os.getenv(
    "EMAIL_MODE",
    "console",
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "",
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587",
    )
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME",
    "",
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD",
    "",
)

SMTP_FROM = os.getenv(
    "SMTP_FROM",
    SMTP_USERNAME,
)

SMTP_SECURITY = os.getenv(
    "SMTP_SECURITY",
    "starttls",
)


class EmailDeliveryError(RuntimeError):
    pass


def build_verification_link(
    token: str,
) -> str:

    query = urlencode({
        "token": token,
    })

    return (
        f"{FRONTEND_URL.rstrip('/')}"
        f"/verify-email?{query}"
    )


def send_verification_email(
    email: str,
    token: str,
) -> None:

    link = build_verification_link(
        token
    )

    # Локальная разработка
    if EMAIL_MODE == "console":
        print()
        print("=" * 60)
        print("EMAIL VERIFICATION")
        print(f"To: {email}")
        print(link)
        print("=" * 60)
        print()

        return

    if EMAIL_MODE != "smtp":
        raise EmailDeliveryError(
            f"Unsupported EMAIL_MODE: {EMAIL_MODE}"
        )

    if not SMTP_HOST:
        raise EmailDeliveryError(
            "SMTP_HOST is not configured"
        )

    if not SMTP_FROM:
        raise EmailDeliveryError(
            "SMTP_FROM is not configured"
        )

    message = EmailMessage()

    message["Subject"] = (
        "Подтверждение регистрации Meditron"
    )

    message["From"] = SMTP_FROM
    message["To"] = email

    message.set_content(
        "Подтвердите адрес электронной почты.\n\n"
        f"{link}\n\n"
        "Если вы не регистрировались в Meditron, "
        "проигнорируйте это письмо."
    )

    try:

        if SMTP_SECURITY == "ssl":

            with smtplib.SMTP_SSL(
                SMTP_HOST,
                SMTP_PORT,
                timeout=10,
            ) as server:

                if SMTP_USERNAME:
                    server.login(
                        SMTP_USERNAME,
                        SMTP_PASSWORD,
                    )

                server.send_message(
                    message
                )

        else:

            with smtplib.SMTP(
                SMTP_HOST,
                SMTP_PORT,
                timeout=10,
            ) as server:

                if SMTP_SECURITY == "starttls":
                    server.starttls()

                if SMTP_USERNAME:
                    server.login(
                        SMTP_USERNAME,
                        SMTP_PASSWORD,
                    )

                server.send_message(
                    message
                )

    except Exception as error:
        raise EmailDeliveryError(
            "Failed to send verification email"
        ) from error

def build_password_reset_link(
    token: str,
) -> str:
    """
    Ссылка, которую пользователь получает
    для восстановления пароля.
    """

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    ).rstrip("/")

    return (
        f"{frontend_url}"
        f"/reset-password"
        f"?token={token}"
    )


def send_password_reset_email(
    email: str,
    token: str,
) -> None:
    """
    Отправляет пользователю ссылку
    восстановления пароля.

    В режиме console ссылка просто
    выводится в терминал.
    """

    reset_link = (
        build_password_reset_link(
            token
        )
    )

    email_mode = os.getenv(
        "EMAIL_MODE",
        "console",
    ).lower()

    # ========================================================
    # DEVELOPMENT
    # ========================================================

    if email_mode == "console":

        print()
        print(
            "PASSWORD RESET EMAIL"
        )
        print(
            "To:",
            email,
        )
        print(
            "Reset password:",
            reset_link,
        )
        print()

        return

    # ========================================================
    # SMTP
    # ========================================================

    if email_mode != "smtp":
        raise EmailDeliveryError(
            (
                "Unsupported EMAIL_MODE: "
                f"{email_mode}"
            )
        )

    smtp_host = os.getenv(
        "SMTP_HOST"
    )

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587",
        )
    )

    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    smtp_from = os.getenv(
        "SMTP_FROM"
    )

    if not all(
        [
            smtp_host,
            smtp_username,
            smtp_password,
            smtp_from,
        ]
    ):
        raise EmailDeliveryError(
            "SMTP configuration is incomplete"
        )

    from email.message import EmailMessage
    import smtplib

    message = EmailMessage()

    message[
        "Subject"
    ] = "Password reset"

    message[
        "From"
    ] = smtp_from

    message[
        "To"
    ] = email

    message.set_content(
        (
            "A password reset was requested "
            "for your account.\n\n"
            f"{reset_link}\n\n"
            "If you did not request this, "
            "you can ignore this message."
        )
    )

    try:

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
        ) as smtp:

            smtp.starttls()

            smtp.login(
                smtp_username,
                smtp_password,
            )

            smtp.send_message(
                message
            )

    except Exception as error:
        raise EmailDeliveryError(
            "Could not send password reset email"
        ) from error