import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dfd.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.api import deps  # noqa: E402
from sqlmodel import Session  # noqa: E402
from app.db import engine  # noqa: E402


init_db()


def override_get_db():
    with Session(engine) as session:
        yield session


app.dependency_overrides[deps.get_db] = override_get_db

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_collection_analysis_endpoint():
    payload = {
        "dataset_name": "known_real",
        "records": [
            {"bitrate": 1000, "rc_mode": "cbr"},
            {"bitrate": 1200, "rc_mode": "cbr"},
        ],
    }
    response = client.post("/collections/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_name"] == "known_real"
    assert body["record_count"] == 2
    assert "bitrate" in body["summary"]


def test_detection_endpoint():
    payload = {
        "target_name": "sample.json",
        "real_summary": {
            "bitrate": {"type": "numeric", "mean": 1000, "median": 1000, "range": 100, "missing": 0}
        },
        "fake_summary": {
            "bitrate": {"type": "numeric", "mean": 2000, "median": 2000, "range": 100, "missing": 0}
        },
        "target_metadata": {"bitrate": 2200},
    }
    response = client.post("/detections/check", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "FAKE"
    assert body["total_rules"] >= 1
    assert body["triggered_rules"] >= 1
    assert len(body["rules"]) == body["total_rules"]
