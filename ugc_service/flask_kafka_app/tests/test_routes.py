# ugc_sprint_1/flask_kafka_app/tests/test_routes.py
import pytest

# from flask import Flask
from app import create_app

# from flask_kafka_app.app.schemas.event import Event
# from kafka import KafkaProducer


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_track_event(client):
    event_data = {
        "user_id": "8e9e106e-ad52-479c-8e2c-a2cb7dee5a07",
        "event_type": "click",
        "timestamp": "2023-10-01T12:00:00Z",
        "fingerprint": "dummy_fingerprint",
        "element": "button",
        "page_url": "https://example.com/page",
    }

    response = client.post("/v1/track_event", json=event_data)
    assert response.status_code == 200
    assert response.json["status"] == "click event tracked"


def test_invalid_event(client):
    # Missing required field user_id
    event_data = {
        "event_type": "click",
        "timestamp": "2023-10-01T12:00:00Z",
        "fingerprint": "dummy_fingerprint",
        "element": "button",
        "page_url": "https://example.com/page",
    }

    response = client.post("/v1/track_event", json=event_data)
    assert response.status_code == 400
    assert "Invalid data" in response.json["error"]
