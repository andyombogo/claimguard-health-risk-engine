"""Rule runner for the ClaimGuard validation engine."""

from __future__ import annotations

import pandas as pd

from src.rules._shared import RULE_OUTPUT_COLUMNS
from src.rules.abnormal_billing import flag_abnormal_billing
from src.rules.diagnosis_treatment_check import flag_diagnosis_treatment_mismatch
from src.rules.document_completeness import flag_missing_documents
from src.rules.duplicate_claims import flag_exact_duplicates, flag_near_duplicates
from src.rules.provider_pattern_check import flag_provider_pattern_risk


def run_all_rules(df: pd.DataFrame, include_all: bool = False) -> pd.DataFrame:
    """Run all available validation rules and return a long-format flags table."""

    rule_outputs = [
        flag_exact_duplicates(df),
        flag_near_duplicates(df),
        flag_abnormal_billing(df),
        flag_diagnosis_treatment_mismatch(df),
        flag_provider_pattern_risk(df),
        flag_missing_documents(df),
    ]
    combined_df = pd.concat(rule_outputs, ignore_index=True)

    if not include_all:
        combined_df = combined_df.loc[combined_df["flag_status"]].copy()

    if combined_df.empty:
        return pd.DataFrame(columns=RULE_OUTPUT_COLUMNS)

    return combined_df.sort_values(
        by=["claim_id", "points", "rule_name"],
        ascending=[True, False, True],
    ).reset_index(drop=True)
