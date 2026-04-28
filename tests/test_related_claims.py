"""Tests for reviewer-facing related-claim context."""

from __future__ import annotations

import pandas as pd

from src.workflow.related_claims import find_related_claims


def _claims_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "claim_id": "CLM-1",
                "member_id": "MBR-1",
                "provider_id": "PRV-1",
                "provider_name": "Demo Clinic",
                "diagnosis_code": "J18",
                "diagnosis_description": "Pneumonia",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_date": "2026-04-10",
                "claim_amount": 10000,
                "total_risk_score": 50,
                "risk_band": "High Risk",
            },
            {
                "claim_id": "CLM-2",
                "member_id": "MBR-1",
                "provider_id": "PRV-1",
                "provider_name": "Demo Clinic",
                "diagnosis_code": "J18",
                "diagnosis_description": "Pneumonia",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_date": "2026-04-14",
                "claim_amount": 10300,
                "total_risk_score": 45,
                "risk_band": "Medium Risk",
            },
            {
                "claim_id": "CLM-3",
                "member_id": "MBR-1",
                "provider_id": "PRV-9",
                "provider_name": "Other Clinic",
                "diagnosis_code": "A09",
                "diagnosis_description": "Gastroenteritis",
                "procedure_code": "PRC-CBC",
                "claim_date": "2026-05-20",
                "claim_amount": 4000,
                "total_risk_score": 5,
                "risk_band": "Low Risk",
            },
            {
                "claim_id": "CLM-4",
                "member_id": "MBR-9",
                "provider_id": "PRV-9",
                "provider_name": "Other Clinic",
                "diagnosis_code": "A09",
                "diagnosis_description": "Gastroenteritis",
                "procedure_code": "PRC-CBC",
                "claim_date": "2026-04-12",
                "claim_amount": 4000,
                "total_risk_score": 0,
                "risk_band": "Low Risk",
            },
        ]
    )


def test_near_duplicate_context_is_prioritized() -> None:
    related_df = find_related_claims(_claims_frame(), "CLM-1")

    assert related_df.iloc[0]["claim_id"] == "CLM-2"
    assert related_df.iloc[0]["relationship_hint"] == "Near-duplicate review context"
    assert related_df.iloc[0]["amount_difference_pct"] == 2.91


def test_same_member_recent_history_is_included_without_calling_it_duplicate() -> None:
    related_df = find_related_claims(_claims_frame(), "CLM-1")
    member_history = related_df.loc[related_df["claim_id"] == "CLM-3"].iloc[0]

    assert member_history["relationship_hint"] == "Same member recent history"


def test_unrelated_claims_are_excluded() -> None:
    related_df = find_related_claims(_claims_frame(), "CLM-1")

    assert "CLM-4" not in related_df["claim_id"].tolist()
