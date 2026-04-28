"""Unit tests for diagnosis/procedure and document rule outputs."""

from __future__ import annotations

import pandas as pd

from src.rules.diagnosis_treatment_check import flag_diagnosis_treatment_mismatch
from src.rules.document_completeness import flag_missing_documents
from src.rules.run_all_rules import run_all_rules


def test_valid_diagnosis_treatment_pair_is_not_flagged() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-201",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
            }
        ]
    )

    flagged_df = flag_diagnosis_treatment_mismatch(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-201", "flag_status"]) is False


def test_invalid_diagnosis_treatment_pair_is_flagged() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-202",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-DENTAL-EXAM",
            }
        ]
    )

    flagged_df = flag_diagnosis_treatment_mismatch(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-202", "flag_status"]) is True
    assert int(flagged_df.loc["CLM-202", "points"]) == 20
    assert "expected list" in flagged_df.loc["CLM-202", "explanation"]


def test_missing_one_document_assigns_low_points_and_complete_claim_is_unflagged() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-301",
                "has_invoice": False,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
            {
                "claim_id": "CLM-302",
                "has_invoice": True,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
        ]
    )

    flagged_df = flag_missing_documents(claims_df).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-301", "flag_status"]) is True
    assert int(flagged_df.loc["CLM-301", "points"]) == 5
    assert flagged_df.loc["CLM-301", "severity"] == "low"
    assert bool(flagged_df.loc["CLM-302", "flag_status"]) is False


def test_missing_multiple_documents_increases_points() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-303",
                "has_invoice": False,
                "has_discharge_summary": False,
                "has_lab_report": True,
            },
            {
                "claim_id": "CLM-304",
                "has_invoice": False,
                "has_discharge_summary": False,
                "has_lab_report": False,
            },
        ]
    )

    flagged_df = flag_missing_documents(claims_df).set_index("claim_id")

    assert int(flagged_df.loc["CLM-303", "points"]) == 10
    assert flagged_df.loc["CLM-303", "severity"] == "medium"
    assert int(flagged_df.loc["CLM-304", "points"]) == 15
    assert flagged_df.loc["CLM-304", "severity"] == "high"


def test_run_all_rules_returns_expected_long_format_columns() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-401",
                "member_id": "MBR-401",
                "provider_id": "PRV-401",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 10000,
                "claim_date": "2026-04-01",
                "has_invoice": True,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
            {
                "claim_id": "CLM-402",
                "member_id": "MBR-401",
                "provider_id": "PRV-401",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 10000,
                "claim_date": "2026-04-01",
                "has_invoice": False,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
            {
                "claim_id": "CLM-403",
                "member_id": "MBR-403",
                "provider_id": "PRV-403",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-DENTAL-EXAM",
                "claim_amount": 35000,
                "claim_date": "2026-04-03",
                "has_invoice": True,
                "has_discharge_summary": False,
                "has_lab_report": False,
            },
        ]
    )

    flags_df = run_all_rules(claims_df)

    assert not flags_df.empty
    assert {
        "claim_id",
        "rule_name",
        "flag_status",
        "severity",
        "points",
        "explanation",
    }.issubset(flags_df.columns)
    assert {"exact_duplicate_claim", "missing_documents", "diagnosis_treatment_mismatch"}.issubset(
        set(flags_df["rule_name"])
    )
