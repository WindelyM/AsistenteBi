"""Test mínimo de integración del endpoint /health."""

import os

# Asegurar DATABASE_URL para que el import de main no falle en CI/tests
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health devuelve 200 y status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
