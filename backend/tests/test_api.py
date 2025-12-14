from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_agent_mock():
    r = client.post("/agent/chat", json={"message": "hello"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["trace"] == []

def test_agent_calculator_trace():
    r = client.post("/agent/chat", json={"message": "calculate 19*23"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "437"
    assert len(data["trace"]) == 1
    assert data["trace"][0]["tool"] == "calculator"
