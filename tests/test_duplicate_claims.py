"""Unit tests for duplicate-claim detection rules."""

from __future__ import annotations

import pandas as pd

from src.rules.duplicate_claims import flag_exact_duplicates, flag_near_duplicates


def test_exact_duplicate_claims_are_flagged() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-001",
                "member_id": "MBR-001",
                "provider_id": "PRV-001",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 15000,
                "claim_date": "2026-04-01",
            },
            {
                "claim_id": "CLM-002",
                "member_id": "MBR-001",
                "provider_id": "PRV-001",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 15000,
                "claim_date": "2026-04-01",
            },
        ]
    )

    flagged_df = flag_exact_duplicates(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-001", "flag_status"]) is True
    assert bool(flagged_df.loc["CLM-002", "flag_status"]) is True
    assert int(flagged_df.loc["CLM-001", "points"]) == 30
    assert "CLM-002" in flagged_df.loc["CLM-001", "explanation"]


def test_near_duplicates_within_window_and_tolerance_are_flagged() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-010",
                "member_id": "MBR-010",
                "provider_id": "PRV-010",
                "diagnosis_code": "A09",
                "procedure_code": "PRC-IV-FLUID",
                "claim_amount": 10000,
                "claim_date": "2026-04-01",
            },
            {
                "claim_id": "CLM-011",
                "member_id": "MBR-010",
                "provider_id": "PRV-010",
                "diagnosis_code": "A09",
                "procedure_code": "PRC-IV-FLUID",
                "claim_amount": 10400,
                "claim_date": "2026-04-10",
            },
        ]
    )

    flagged_df = flag_near_duplicates(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-010", "flag_status"]) is True
    assert bool(flagged_df.loc["CLM-011", "flag_status"]) is True
    assert int(flagged_df.loc["CLM-010", "points"]) == 20
    assert flagged_df.loc["CLM-010", "severity"] == "medium"


def test_claims_outside_date_window_are_not_flagged_as_near_duplicates() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-020",
                "member_id": "MBR-020",
                "provider_id": "PRV-020",
                "diagnosis_code": "N39",
                "procedure_code": "PRC-URINE-CULTURE",
                "claim_amount": 12000,
                "claim_date": "2026-03-01",
            },
            {
                "claim_id": "CLM-021",
                "member_id": "MBR-020",
                "provider_id": "PRV-020",
                "diagnosis_code": "N39",
                "procedure_code": "PRC-URINE-CULTURE",
                "claim_amount": 12400,
                "claim_date": "2026-03-20",
            },
        ]
    )

    flagged_df = flag_near_duplicates(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-020", "flag_status"]) is False
    assert bool(flagged_df.loc["CLM-021", "flag_status"]) is False


def test_claims_with_different_members_are_not_flagged_as_duplicates() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-030",
                "member_id": "MBR-030",
                "provider_id": "PRV-030",
                "diagnosis_code": "M54",
                "procedure_code": "PRC-PHYSIO-SESSION",
                "claim_amount": 9000,
                "claim_date": "2026-04-05",
            },
            {
                "claim_id": "CLM-031",
                "member_id": "MBR-031",
                "provider_id": "PRV-030",
                "diagnosis_code": "M54",
                "procedure_code": "PRC-PHYSIO-SESSION",
                "claim_amount": 9000,
                "claim_date": "2026-04-05",
            },
        ]
    )

    exact_df = flag_exact_duplicates(claims_df).set_index("claim_id")
    near_df = flag_near_duplicates(claims_df).set_index("claim_id")

    assert bool(exact_df.loc["CLM-030", "flag_status"]) is False
    assert bool(exact_df.loc["CLM-031", "flag_status"]) is False
    assert bool(near_df.loc["CLM-030", "flag_status"]) is False
    assert bool(near_df.loc["CLM-031", "flag_status"]) is False
