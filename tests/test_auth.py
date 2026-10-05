import uuid
from api.database.database import SessionLocal
from api.services.auth_service import (
    register_user,
    verify_email,
)
from fastapi.testclient import TestClient
from api.database.models import User
from api.main import app


client = TestClient(app)


def unique_email(prefix: str) -> str:
    return (
        f"{prefix}-"
        f"{uuid.uuid4().hex}"
        "@example.com"
    )


def test_register_patient():
    email = unique_email("patient")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "role": "patient",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user"]["email"] == email
    assert data["user"]["role"] == "patient"
    assert data["user"]["is_email_verified"] is False

    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_doctor():
    email = unique_email("doctor")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "role": "doctor",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user"]["role"] == "doctor"


def test_duplicate_email():
    email = unique_email("duplicate")

    payload = {
        "email": email,
        "password": "TestPassword123!",
        "role": "patient",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong-email",
            "password": "TestPassword123!",
            "role": "patient",
        },
    )

    assert response.status_code == 422


def test_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email("short"),
            "password": "123",
            "role": "patient",
        },
    )

    assert response.status_code == 422


def test_invalid_role():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email("role"),
            "password": "TestPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422

def test_verify_email():
    email = unique_email(
        "verify"
    )

    db = SessionLocal()

    user, raw_token = register_user(
        db,
        email=email,
        password="TestPassword123!",
        role="patient",
    )

    user_id = user.id

    db.close()

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": raw_token,
        },
    )

    assert response.status_code == 200

    db = SessionLocal()

    user = db.get(
        User,
        user_id,
    )

    assert (
        user.is_email_verified
        is True
    )

    db.close()

def test_verify_email_invalid_token():
    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": (
                "this-token-does-not-exist-123456"
            )
        },
    )

    assert response.status_code == 400


def test_resend_verification():
    email = unique_email(
        "resend"
    )

    db = SessionLocal()

    register_user(
        db,
        email=email,
        password="TestPassword123!",
        role="patient",
    )

    db.close()

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": email,
        },
    )

    assert response.status_code == 200


def test_resend_unknown_email():
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": unique_email(
                "unknown"
            )
        },
    )

    assert response.status_code == 200

def create_verified_user(
    email: str,
    password: str = "TestPassword123!",
    role: str = "patient",
):
    db = SessionLocal()

    user, token = register_user(
        db,
        email=email,
        password=password,
        role=role,
    )

    verify_email(
        db,
        raw_token=token,
    )

    db.close()

def test_login():
    email = unique_email(
        "login"
    )

    password = "TestPassword123!"

    create_verified_user(
        email,
        password,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["token_type"]
        == "bearer"
    )

    assert len(
        data["access_token"]
    ) > 20

    assert (
        data["user"]["email"]
        == email
    )

def test_login_wrong_password():
    email = unique_email(
        "wrong-password"
    )

    create_verified_user(
        email
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

def test_login_unverified_email():
    email = unique_email(
        "unverified"
    )

    db = SessionLocal()

    register_user(
        db,
        email=email,
        password="TestPassword123!",
        role="patient",
    )

    db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 403

def test_get_me():
    email = unique_email(
        "me"
    )

    password = "TestPassword123!"

    create_verified_user(
        email,
        password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["email"]
        == email
    )

def test_get_me_without_auth():
    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_logout_revokes_session():
    email = unique_email(
        "logout"
    )

    password = "TestPassword123!"

    create_verified_user(
        email,
        password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    token = login_response.json()[
        "access_token"
    ]

    headers = {
        "Authorization": (
            f"Bearer {token}"
        )
    }

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers=headers,
    )

    assert (
        logout_response.status_code
        == 200
    )

    me_response = client.get(
        "/api/v1/auth/me",
        headers=headers,
    )

    assert (
        me_response.status_code
        == 401
    )