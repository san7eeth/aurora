"""Unit tests — FastAPI REST endpoints."""
import pytest


def test_health_returns_200(test_client):
    r = test_client.get("/health")
    assert r.status_code == 200


def test_health_body_has_status_ok(test_client):
    r = test_client.get("/health")
    assert r.json()["status"] == "ok"


def test_health_body_has_model(test_client):
    r = test_client.get("/health")
    assert "model" in r.json()


def test_health_body_has_version(test_client):
    r = test_client.get("/health")
    assert "version" in r.json()


def test_select_model_empty_name_returns_400(test_client):
    r = test_client.post("/api/models/select", json={"model": ""})
    assert r.status_code == 400
    assert "error" in r.json()


def test_select_model_valid_name_returns_200(test_client):
    r = test_client.post("/api/models/select", json={"model": "phi3:mini"})
    assert r.status_code == 200
    assert r.json()["active"] == "phi3:mini"


def test_select_model_missing_body_returns_400(test_client):
    r = test_client.post("/api/models/select", json={})
    assert r.status_code == 400
