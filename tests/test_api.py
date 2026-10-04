from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from api.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "Meditron API"
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["api"] == "ok"
    assert data["ml_bundle_loaded"] is True
    assert data["expert_engine_available"] is True
    assert data["bundle_version"] is not None


def test_features_metadata():
    response = client.get("/api/v1/meta/features")

    assert response.status_code == 200

    data = response.json()

    assert data["n_features"] == 37
    assert len(data["features"]) == 37

    assert "sex" in data["features"]
    assert "hemoglobin" in data["features"]
    assert "ferritin" in data["features"]

    assert "sex" in data["categorical_features"]

    assert len(data["targets"]) == 6
    assert "iron_deficiency" in data["targets"]
    assert "B12_deficiency" in data["targets"]


def test_model_metadata():
    response = client.get("/api/v1/meta/model")

    assert response.status_code == 200

    data = response.json()

    assert data["bundle_name"] == "meditron_frozen_inference_bundle"
    assert data["bundle_version"] == "1.0"

    assert data["n_features"] == 37

    assert "targets" in data
    assert len(data["targets"]) == 6

    assert "architecture" in data


def test_screening_success():
    payload = {
        "patient_id": "test-patient-001",
        "features": {
            "sex": "F",
            "hemoglobin": 108,
            "MCV": 74,
            "MCH": 23,
            "ferritin": 8.0,
            "serum_iron": 7.5,
            "TIBC": 82,
            "TSAT": 10,
        },
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["patient_id"] == "test-patient-001"

    assert "screening_id" in data
    assert isinstance(data["screening_id"], str)
    assert len(data["screening_id"]) > 0

    assert "prediction" in data

    assert "anemia" in data["prediction"]
    assert "anemia_class" in data["prediction"]
    assert "deficiency_cause" in data["prediction"]

    assert "confidence" in data
    assert "certainty" in data["confidence"]
    assert "level" in data["confidence"]

    assert "deficiencies" in data

    expected_targets = {
        "iron_deficiency",
        "B12_deficiency",
        "folate_deficiency",
        "B6_deficiency",
        "copper_deficiency",
        "inflammation_anemia",
    }

    assert set(data["deficiencies"].keys()) == expected_targets

    for target in expected_targets:
        result = data["deficiencies"][target]

        assert 0.0 <= result["probability"] <= 1.0
        assert 0.0 <= result["threshold"] <= 1.0
        assert isinstance(result["prediction"], bool)

    assert "data_quality" in data
    assert 0.0 <= data["data_quality"]["coverage"] <= 1.0

    assert "evidence" in data
    assert "conflicts" in data
    assert "recommended_next_tests" in data

    assert "model" in data
    assert data["model"]["bundle_version"] == "1.0"

    assert "disclaimer" in data


def test_screening_wrong_sex():
    payload = {
        "features": {
            "sex": "X",
            "hemoglobin": 120,
        }
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 422


def test_screening_without_hemoglobin():
    payload = {
        "features": {
            "sex": "F",
            "ferritin": 10,
        }
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 422


def test_low_coverage_returns_warning():
    payload = {
        "features": {
            "sex": "F",
            "hemoglobin": 110,
            "ferritin": 8,
        }
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["data_quality"]["coverage"] < 0.70
    assert len(data["data_quality"]["warnings"]) > 0

def test_cors_for_frontend():
    response = client.options(
        "/api/v1/screenings",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )

def test_cors_rejects_unknown_origin():
    response = client.options(
        "/api/v1/screenings",
        headers={
            "Origin": "http://localhost:9999",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400

    assert (
        response.headers.get(
            "access-control-allow-origin"
        )
        is None
    )

def test_screening_rejects_unknown_feature():
    payload = {
        "features": {
            "sex": "F",
            "hemoglobin": 120,
            "unknown_lab": 123,
        }
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 422

def test_screening_without_sex():
    payload = {
        "features": {
            "hemoglobin": 110,
            "ferritin": 8,
        }
    }

    response = client.post(
        "/api/v1/screenings",
        json=payload,
    )

    assert response.status_code == 422