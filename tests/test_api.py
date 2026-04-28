"""Tests for the optional FastAPI demo endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


CLIENT = TestClient(app)
EXAMPLE_REQUEST_PATH = Path(__file__).resolve().parents[1] / "api" / "examples" / "score_claim_request.json"


def test_health_endpoint_returns_ok() -> None:
    response = CLIENT.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_root_endpoint_includes_responsible_use_note() -> None:
    response = CLIENT.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "ClaimGuard Health Risk Engine API"
    assert "does not confirm fraud" in payload["responsible_use_note"]


def test_score_claim_endpoint_returns_review_prioritization_payload() -> None:
    request_payload = json.loads(EXAMPLE_REQUEST_PATH.read_text(encoding="utf-8"))

    response = CLIENT.post("/score-claim", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_id"] == request_payload["claim_id"]
    assert payload["total_risk_score"] >= 0
    assert payload["risk_band"] in {"Low Risk", "Medium Risk", "High Risk", "Critical Risk"}
    assert payload["recommended_action"]
    assert isinstance(payload["flags"], list)
    assert "human assessment only" in payload["disclaimer"]
    assert "limited because no historical claim list" in payload["explanation"]


def test_score_claim_rejects_negative_amounts() -> None:
    request_payload = json.loads(EXAMPLE_REQUEST_PATH.read_text(encoding="utf-8"))
    request_payload["claim_amount"] = -1

    response = CLIENT.post("/score-claim", json=request_payload)

    assert response.status_code == 422
