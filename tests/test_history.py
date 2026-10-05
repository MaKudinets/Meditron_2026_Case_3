import uuid

from fastapi.testclient import TestClient

from api.database.database import (
    SessionLocal,
)
from api.main import app

from api.services.auth_service import (
    register_user,
    verify_email,
)


client = TestClient(
    app
)


PASSWORD = "TestPassword123!"


def unique_email(
    prefix: str,
) -> str:

    return (
        f"{prefix}-"
        f"{uuid.uuid4().hex}"
        "@example.com"
    )


def create_patient_and_login():
    email = unique_email(
        "history"
    )

    db = SessionLocal()

    user, verification_token = (
        register_user(
            db,
            email=email,
            password=PASSWORD,
            role="patient",
        )
    )

    verify_email(
        db,
        raw_token=(
            verification_token
        ),
    )

    db.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )

    assert (
        login_response.status_code
        == 200
    )

    token = login_response.json()[
        "access_token"
    ]

    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


def screening_payload():
    return {
        "features": {
            "sex": "F",
            "hemoglobin": 108,
            "MCV": 74,
            "MCH": 23,
            "ferritin": 8,
            "serum_iron": 7.5,
            "TIBC": 82,
            "TSAT": 10,
        }
    }


def test_create_saved_screening():
    headers = (
        create_patient_and_login()
    )

    response = client.post(
        "/api/v1/me/screenings",
        json=screening_payload(),
        headers=headers,
    )

    assert (
        response.status_code
        == 201
    )

    data = response.json()

    assert "screening_id" in data

    assert (
        data["prediction"]
        is not None
    )


def test_screening_appears_in_history():
    headers = (
        create_patient_and_login()
    )

    create_response = client.post(
        "/api/v1/me/screenings",
        json=screening_payload(),
        headers=headers,
    )

    screening_id = (
        create_response.json()[
            "screening_id"
        ]
    )

    response = client.get(
        "/api/v1/me/screenings",
        headers=headers,
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    ids = {
        item["screening_id"]
        for item in data["items"]
    }

    assert screening_id in ids


def test_get_saved_screening():
    headers = (
        create_patient_and_login()
    )

    create_response = client.post(
        "/api/v1/me/screenings",
        json=screening_payload(),
        headers=headers,
    )

    screening_id = (
        create_response.json()[
            "screening_id"
        ]
    )

    response = client.get(
        (
            "/api/v1/me/screenings/"
            f"{screening_id}"
        ),
        headers=headers,
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.json()[
            "screening_id"
        ]
        == screening_id
    )


def test_delete_saved_screening():
    headers = (
        create_patient_and_login()
    )

    create_response = client.post(
        "/api/v1/me/screenings",
        json=screening_payload(),
        headers=headers,
    )

    screening_id = (
        create_response.json()[
            "screening_id"
        ]
    )

    response = client.delete(
        (
            "/api/v1/me/screenings/"
            f"{screening_id}"
        ),
        headers=headers,
    )

    assert (
        response.status_code
        == 200
    )

    response = client.get(
        (
            "/api/v1/me/screenings/"
            f"{screening_id}"
        ),
        headers=headers,
    )

    assert (
        response.status_code
        == 404
    )