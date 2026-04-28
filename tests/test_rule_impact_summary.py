"""Tests for rule-impact calibration summaries."""

from __future__ import annotations

import pandas as pd

from src.rules.rule_impact_summary import build_rule_impact_summary, build_risk_band_summary


def test_rule_impact_summary_counts_triggered_rules() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1",
                "member_id": "MBR-1",
                "provider_id": "PRV-1",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 10000,
                "claim_date": "2026-04-01",
                "has_invoice": False,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
            {
                "claim_id": "CLM-2",
                "member_id": "MBR-2",
                "provider_id": "PRV-2",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-DENTAL-EXAM",
                "claim_amount": 12000,
                "claim_date": "2026-04-02",
                "has_invoice": True,
                "has_discharge_summary": True,
                "has_lab_report": True,
            },
        ]
    )

    summary_df = build_rule_impact_summary(claims_df)

    assert {"missing_documents", "diagnosis_treatment_mismatch"}.issubset(
        set(summary_df["rule_name"])
    )
    assert int(summary_df["flagged_claims"].sum()) >= 2


def test_risk_band_summary_returns_claim_counts() -> None:
    claims_df = pd.DataFrame(
        [
            {
                "claim_id": "CLM-1",
                "member_id": "MBR-1",
                "provider_id": "PRV-1",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 10000,
                "claim_date": "2026-04-01",
                "has_invoice": True,
                "has_discharge_summary": True,
                "has_lab_report": True,
            }
        ]
    )

    summary_df = build_risk_band_summary(claims_df)

    assert int(summary_df["claim_count"].sum()) == 1
