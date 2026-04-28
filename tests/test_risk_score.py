"""Unit tests for claim-level risk scoring outputs."""

from __future__ import annotations

import pandas as pd

from src.scoring.risk_band import assign_recommended_action, assign_risk_band
from src.scoring.risk_score import calculate_risk_scores, score_claims


def test_calculate_risk_scores_aggregates_points_correctly() -> None:
    claims_df = pd.DataFrame({"claim_id": ["CLM-1", "CLM-2", "CLM-3"]})
    flags_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1",
                "rule_name": "missing_documents",
                "flag_status": True,
                "severity": "low",
                "points": 5,
                "explanation": "One document missing.",
            },
            {
                "claim_id": "CLM-2",
                "rule_name": "abnormal_billing",
                "flag_status": True,
                "severity": "high",
                "points": 25,
                "explanation": "Billing above threshold.",
            },
            {
                "claim_id": "CLM-2",
                "rule_name": "near_duplicate_claim",
                "flag_status": True,
                "severity": "medium",
                "points": 20,
                "explanation": "Near duplicate pattern.",
            },
        ]
    )

    scored_df = calculate_risk_scores(claims_df, flags_df).set_index("claim_id")

    assert int(scored_df.loc["CLM-1", "total_risk_score"]) == 5
    assert int(scored_df.loc["CLM-2", "total_risk_score"]) == 45
    assert int(scored_df.loc["CLM-2", "number_of_flags"]) == 2
    assert int(scored_df.loc["CLM-3", "total_risk_score"]) == 0


def test_calculate_risk_scores_caps_total_at_100() -> None:
    claims_df = pd.DataFrame({"claim_id": ["CLM-9"]})
    flags_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-9",
                "rule_name": "provider_pattern_risk",
                "flag_status": True,
                "severity": "critical",
                "points": 80,
                "explanation": "Provider pattern review recommended.",
            },
            {
                "claim_id": "CLM-9",
                "rule_name": "abnormal_billing",
                "flag_status": True,
                "severity": "critical",
                "points": 50,
                "explanation": "Billing above threshold.",
            },
        ]
    )

    scored_df = calculate_risk_scores(claims_df, flags_df)

    assert int(scored_df.loc[0, "total_risk_score"]) == 100
    assert scored_df.loc[0, "risk_band"] == "Critical Risk"


def test_assign_risk_band_and_recommended_action_cover_all_boundaries() -> None:
    assert assign_risk_band(0) == "Low Risk"
    assert assign_risk_band(24) == "Low Risk"
    assert assign_risk_band(25) == "Medium Risk"
    assert assign_risk_band(49) == "Medium Risk"
    assert assign_risk_band(50) == "High Risk"
    assert assign_risk_band(74) == "High Risk"
    assert assign_risk_band(75) == "Critical Risk"
    assert assign_risk_band(100) == "Critical Risk"

    assert assign_recommended_action("Low Risk") == "Fast-track standard review"
    assert assign_recommended_action("Medium Risk") == (
        "Standard review with attention to flagged items"
    )
    assert assign_recommended_action("High Risk") == "Maker-checker review required"
    assert assign_recommended_action("Critical Risk") == (
        "Escalate for detailed investigation before approval"
    )


def test_score_claims_returns_zero_scores_and_compatibility_columns_when_unflagged() -> None:
    claims_df = pd.DataFrame(
        [
            {"claim_id": "CLM-10"},
            {"claim_id": "CLM-11"},
        ]
    )
    flags_df = pd.DataFrame(
        columns=[
            "claim_id",
            "rule_name",
            "flag_status",
            "severity",
            "points",
            "explanation",
        ]
    )

    scored_df = score_claims(claims_df, flags_df).set_index("claim_id")

    assert int(scored_df.loc["CLM-10", "total_risk_score"]) == 0
    assert scored_df.loc["CLM-10", "risk_band"] == "Low Risk"
    assert scored_df.loc["CLM-10", "recommended_action"] == "Fast-track standard review"
    assert scored_df.loc["CLM-10", "triggered_rules"] == "none"
    assert bool(scored_df.loc["CLM-10", "requires_escalation"]) is False
