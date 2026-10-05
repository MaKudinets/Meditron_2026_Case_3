from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Хеширует пароль перед сохранением в БД.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    Проверяет пароль пользователя.
    """
    return password_hasher.verify(
        plain_password,
        password_hash,
    )