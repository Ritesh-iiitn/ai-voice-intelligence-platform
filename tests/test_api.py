"""Integration tests for FastAPI endpoints and WebSocket live streaming."""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from q4_realtime.schemas import SpeakerRole


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "q4_realtime" in data["modules"]


def test_kb_search_api(client):
    res = client.post(
        "/api/kb/search",
        json={"query": "minimum income for auto loan", "top_k": 2},
    )
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "citations" in data


def test_voice_turn_api(client):
    res = client.post(
        "/api/voice/process-turn",
        json={"call_id": "test-api-call-1", "customer_speech": "Hello, I want an auto loan."},
    )
    assert res.status_code == 200
    data = res.json()
    assert "agent_response" in data
    assert data["current_state"] in ["CONSENT", "COLLECT_DETAILS", "GREETING"]


def test_multilingual_route_api(client):
    res_ph = client.post(
        "/api/multilingual/route",
        json={"text": "Magkano po ba ang monthly premium para sa loan protection?"},
    )
    assert res_ph.status_code == 200
    assert res_ph.json()["market"] == "PH"

    res_id = client.post(
        "/api/multilingual/route",
        json={"text": "Berapa cicilan per bulan dan tenor angsuran untuk kredit mobil?"},
    )
    assert res_id.status_code == 200
    assert res_id.json()["market"] == "ID"


def test_simulate_stream_turn_cross_sell(client):
    res = client.post(
        "/api/calls/simulate-turn",
        json={
            "call_id": "api-stream-call-99",
            "speaker": SpeakerRole.CUSTOMER,
            "text": "I also want to add a second car for my daughter.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert len(data["signals_detected"]) >= 1
    assert data["signals_detected"][0]["signal_type"] == "missed_cross_sell"
    assert len(data["nudges_generated"]) >= 1
    assert not data["nudges_generated"][0]["suppressed"]


def test_websocket_stream_connection(client):
    with client.websocket_connect("/ws/calls/test-ws-call") as websocket:
        websocket.send_json({"event_type": "ping"})
        data = websocket.receive_json()
        assert data["event_type"] == "pong"


def test_reset_call_api(client):
    res = client.post("/api/calls/reset", json={"call_id": "test-reset-call"})
    assert res.status_code == 200
    assert res.json()["status"] == "reset"
    assert res.json()["call_id"] == "test-reset-call"

