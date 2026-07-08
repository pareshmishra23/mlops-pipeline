import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert "model_version" in response.json()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_predict_success(client):
    payload = {"features": [5.1, 3.5, 1.4, 0.2]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert "model_version" in data
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_invalid_features_length(client):
    # Model wrapper expects exactly 4 features
    payload = {"features": [5.1, 3.5, 1.4]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_predict_invalid_features_type(client):
    # Schema expects floats
    payload = {"features": ["not", "a", "float", "list"]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
