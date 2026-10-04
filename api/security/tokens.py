# Сам токен отправляется пользователю, но в БД храним только его SHA-256 hash. Это полезно на случай утечки БД: сырого токена подтверждения там не будет.
import hashlib
import secrets


def generate_token() -> str:
    """
    Создаёт криптографически случайный токен.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Хеширует токен перед сохранением в БД.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()