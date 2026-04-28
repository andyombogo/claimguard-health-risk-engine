"""Unit tests for abnormal billing detection."""

from __future__ import annotations

import pandas as pd

from src.rules.abnormal_billing import flag_abnormal_billing


def _build_billing_test_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "claim_id": "CLM-100",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 10000,
            },
            {
                "claim_id": "CLM-101",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 12000,
            },
            {
                "claim_id": "CLM-102",
                "diagnosis_code": "J18",
                "procedure_code": "PRC-CHEST-XRAY",
                "claim_amount": 30000,
            },
            {
                "claim_id": "CLM-103",
                "diagnosis_code": "K02",
                "procedure_code": "PRC-DENTAL-EXAM",
                "claim_amount": 8000,
            },
        ]
    )


def test_claim_above_multiplier_threshold_is_flagged() -> None:
    flagged_df = flag_abnormal_billing(_build_billing_test_frame()).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-102", "flag_status"]) is True
    assert int(flagged_df.loc["CLM-102", "points"]) == 25
    assert "2.50x" in flagged_df.loc["CLM-102", "explanation"] or "2.73x" in flagged_df.loc["CLM-102", "explanation"]


def test_claim_below_threshold_is_not_flagged() -> None:
    flagged_df = flag_abnormal_billing(_build_billing_test_frame()).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-101", "flag_status"]) is False


def test_abnormal_billing_handles_small_groups_gracefully() -> None:
    flagged_df = flag_abnormal_billing(_build_billing_test_frame()).set_index("claim_id")

    assert bool(flagged_df.loc["CLM-103", "flag_status"]) is False
    assert int(flagged_df.loc["CLM-103", "points"]) == 0
