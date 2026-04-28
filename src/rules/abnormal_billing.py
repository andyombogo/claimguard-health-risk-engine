"""Abnormal billing validation rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig
from src.rules._shared import (
    flag_rows_to_findings,
    initialize_rule_output,
    normalize_claims_dataframe,
)

RULE_NAME = "abnormal_billing"
_REQUIRED_COLUMNS = ["claim_id", "diagnosis_code", "procedure_code", "claim_amount"]


def flag_abnormal_billing(
    df: pd.DataFrame,
    multiplier_threshold: float = 2.5,
) -> pd.DataFrame:
    """Flag claims billed far above the median for similar diagnosis-procedure pairs."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, RULE_NAME)
    output_df = initialize_rule_output(normalized_df, RULE_NAME)

    group_medians = normalized_df.groupby(["diagnosis_code", "procedure_code"], dropna=False)[
        "claim_amount"
    ].transform("median")
    multipliers = normalized_df["claim_amount"] / group_medians.where(group_medians > 0)
    flagged_mask = multipliers >= multiplier_threshold

    output_df.loc[flagged_mask, "flag_status"] = True
    output_df.loc[flagged_mask, "points"] = 25
    output_df.loc[flagged_mask, "severity"] = multipliers.loc[flagged_mask].apply(
        lambda value: "critical" if value >= 4 else "high"
    )
    output_df.loc[flagged_mask, "explanation"] = [
        (
            f"Claim amount {claim_amount:,.2f} is {multiplier:.2f}x the median "
            f"amount {median_amount:,.2f} for diagnosis {diagnosis_code} and procedure "
            f"{procedure_code}, so additional billing review is recommended."
        )
        for claim_amount, median_amount, multiplier, diagnosis_code, procedure_code in zip(
            normalized_df.loc[flagged_mask, "claim_amount"],
            group_medians.loc[flagged_mask],
            multipliers.loc[flagged_mask],
            normalized_df.loc[flagged_mask, "diagnosis_code"],
            normalized_df.loc[flagged_mask, "procedure_code"],
        )
    ]

    return output_df


def evaluate_abnormal_billing(
    claim_row: pd.Series,
    claims_df: pd.DataFrame | RiskRulesConfig | None = None,
    rules_config: RiskRulesConfig | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns abnormal billing findings for one claim."""

    if isinstance(claims_df, RiskRulesConfig):
        rules_config = claims_df
        claims_df = None

    if isinstance(claims_df, pd.DataFrame):
        rule_output_df = flag_abnormal_billing(claims_df)
        claim_id = str(claim_row.get("claim_id", ""))
        claim_findings_df = rule_output_df.loc[
            (rule_output_df["claim_id"] == claim_id) & (rule_output_df["flag_status"])
        ]
        return flag_rows_to_findings(claim_findings_df)

    billed_amount = float(claim_row.get("claim_amount", claim_row.get("claimed_amount", 0)) or 0)
    length_of_stay = float(claim_row.get("length_of_stay_days", 0) or 0)
    claim_type = str(claim_row.get("claim_type", "")).lower()
    amount_threshold = 250000
    short_stay_limit = 2

    if rules_config is not None and "abnormal_billing" in rules_config.rules:
        amount_threshold = rules_config.rules["abnormal_billing"].parameters.get(
            "amount_threshold",
            amount_threshold,
        )
        short_stay_limit = rules_config.rules["abnormal_billing"].parameters.get(
            "short_stay_days_max",
            short_stay_limit,
        )

    if claim_type == "inpatient" and billed_amount >= amount_threshold and length_of_stay <= short_stay_limit:
        return [
            {
                "rule_name": RULE_NAME,
                "weight": 25,
                "reason": (
                    "Short inpatient stay billed above the configured threshold and "
                    "should be reviewed."
                ),
                "severity": "high",
            }
        ]

    return []
