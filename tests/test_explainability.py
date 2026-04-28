"""Tests for explainability helpers."""

from __future__ import annotations

import pandas as pd

from src.scoring.explainability import (
    build_claim_risk_profile,
    generate_claim_explanation,
)


def test_generate_claim_explanation_summarizes_rule_labels() -> None:
    flags_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1042",
                "rule_name": "near_duplicate_claim",
                "flag_status": True,
                "severity": "medium",
                "points": 20,
                "explanation": "Similar claim nearby.",
            },
            {
                "claim_id": "CLM-1042",
                "rule_name": "abnormal_billing",
                "flag_status": True,
                "severity": "high",
                "points": 25,
                "explanation": "Billing above median.",
            },
            {
                "claim_id": "CLM-1042",
                "rule_name": "missing_documents",
                "flag_status": True,
                "severity": "low",
                "points": 5,
                "explanation": "Missing discharge summary.",
            },
        ]
    )

    explanation = generate_claim_explanation("CLM-1042", flags_df)

    assert "Claim CLM-1042 is high risk" in explanation
    assert "near duplicate claim" in explanation
    assert "abnormal billing" in explanation
    assert "missing documents" in explanation


def test_build_claim_risk_profile_returns_reviewer_facing_payload() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1042",
                "member_id": "MBR-001",
                "provider_id": "PRV-001",
                "claim_amount": 25000,
            }
        ]
    )
    flags_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1042",
                "rule_name": "abnormal_billing",
                "flag_status": True,
                "severity": "high",
                "points": 25,
                "explanation": "Billing above median.",
            }
        ]
    )

    profile = build_claim_risk_profile(claims_df, flags_df, "CLM-1042")

    assert profile["risk_score"] == 25
    assert profile["risk_band"] == "Medium Risk"
    assert profile["recommended_action"] == "Standard review with attention to flagged items"
    assert profile["flagged_rules"][0]["rule_name"] == "abnormal_billing"
    assert "Reviewer note template" in profile["reviewer_note_template"]
