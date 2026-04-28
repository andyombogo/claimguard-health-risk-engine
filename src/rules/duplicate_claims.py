"""Duplicate and near-duplicate claim validation rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig
from src.rules._shared import (
    flag_rows_to_findings,
    initialize_rule_output,
    normalize_claims_dataframe,
    similar_claim_text,
)

EXACT_DUPLICATE_RULE_NAME = "exact_duplicate_claim"
NEAR_DUPLICATE_RULE_NAME = "near_duplicate_claim"

_REQUIRED_COLUMNS = [
    "claim_id",
    "member_id",
    "provider_id",
    "diagnosis_code",
    "procedure_code",
    "claim_amount",
    "claim_date",
]


def flag_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Flag exact duplicate claims across key identifiers and billing fields."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, EXACT_DUPLICATE_RULE_NAME)
    output_df = initialize_rule_output(normalized_df, EXACT_DUPLICATE_RULE_NAME)

    duplicate_columns = [
        "member_id",
        "provider_id",
        "diagnosis_code",
        "procedure_code",
        "claim_amount",
        "claim_date",
    ]
    duplicated_mask = normalized_df.duplicated(subset=duplicate_columns, keep=False)

    if not duplicated_mask.any():
        return output_df

    duplicated_groups = normalized_df.loc[duplicated_mask].groupby(duplicate_columns, dropna=False)
    for _, group_df in duplicated_groups:
        group_claim_ids = group_df["claim_id"].astype(str).tolist()
        for group_index, claim_row in group_df.iterrows():
            peer_claim_ids = [claim_id for claim_id in group_claim_ids if claim_id != claim_row["claim_id"]]
            output_df.loc[group_index, "flag_status"] = True
            output_df.loc[group_index, "severity"] = "high"
            output_df.loc[group_index, "points"] = 30
            output_df.loc[group_index, "explanation"] = (
                "Claim matches another submission on member, provider, diagnosis, "
                "procedure, amount, and claim date. Similar claim ID(s): "
                f"{similar_claim_text(peer_claim_ids)}."
            )

    return output_df


def flag_near_duplicates(
    df: pd.DataFrame,
    amount_tolerance: float = 0.05,
    date_window_days: int = 14,
) -> pd.DataFrame:
    """Flag claims that appear near-duplicate based on amount and timing tolerance."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, NEAR_DUPLICATE_RULE_NAME)
    output_df = initialize_rule_output(normalized_df, NEAR_DUPLICATE_RULE_NAME)

    exact_duplicate_mask = flag_exact_duplicates(normalized_df)["flag_status"]
    similar_claims_by_id: dict[str, set[str]] = defaultdict(set)

    group_columns = ["member_id", "provider_id", "diagnosis_code", "procedure_code"]
    grouped = normalized_df.groupby(group_columns, dropna=False, sort=False)

    for _, group_df in grouped:
        if len(group_df) < 2:
            continue

        sorted_group_df = group_df.sort_values("claim_date")
        rows = list(sorted_group_df.itertuples())

        for left_index, left_row in enumerate(rows):
            if pd.isna(left_row.claim_date) or pd.isna(left_row.claim_amount):
                continue

            for right_row in rows[left_index + 1 :]:
                if pd.isna(right_row.claim_date) or pd.isna(right_row.claim_amount):
                    continue

                date_difference = abs((right_row.claim_date - left_row.claim_date).days)
                if date_difference > date_window_days:
                    break

                amount_reference = max(float(left_row.claim_amount), float(right_row.claim_amount), 1.0)
                amount_difference_ratio = abs(
                    float(left_row.claim_amount) - float(right_row.claim_amount)
                ) / amount_reference

                is_exact_duplicate = (
                    left_row.claim_date == right_row.claim_date
                    and float(left_row.claim_amount) == float(right_row.claim_amount)
                )
                if is_exact_duplicate:
                    continue

                if amount_difference_ratio <= amount_tolerance:
                    similar_claims_by_id[str(left_row.claim_id)].add(str(right_row.claim_id))
                    similar_claims_by_id[str(right_row.claim_id)].add(str(left_row.claim_id))

    for output_index, claim_id in enumerate(output_df["claim_id"].astype(str).tolist()):
        if exact_duplicate_mask.iloc[output_index]:
            continue

        if claim_id not in similar_claims_by_id:
            continue

        output_df.loc[output_index, "flag_status"] = True
        output_df.loc[output_index, "severity"] = "medium"
        output_df.loc[output_index, "points"] = 20
        output_df.loc[output_index, "explanation"] = (
            "Claim closely resembles another submission for the same member, provider, "
            "diagnosis, and procedure within the configured review window. Similar claim ID(s): "
            f"{similar_claim_text(similar_claims_by_id[claim_id])}."
        )

    return output_df


def evaluate_duplicate_claims(
    claim_row: pd.Series,
    claims_df: pd.DataFrame,
    rules_config: RiskRulesConfig | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns duplicate findings for a single claim."""

    exact_output_df = flag_exact_duplicates(claims_df)
    near_output_df = flag_near_duplicates(claims_df)
    combined_output_df = pd.concat([exact_output_df, near_output_df], ignore_index=True)

    claim_id = str(claim_row.get("claim_id", ""))
    claim_findings_df = combined_output_df.loc[
        (combined_output_df["claim_id"] == claim_id) & (combined_output_df["flag_status"])
    ]
    findings = flag_rows_to_findings(claim_findings_df)
    legacy_name_map = {
        EXACT_DUPLICATE_RULE_NAME: "possible_duplicate_same_day",
        NEAR_DUPLICATE_RULE_NAME: "near_duplicate_amount_pattern",
    }
    for finding in findings:
        finding["rule_name"] = legacy_name_map.get(finding["rule_name"], finding["rule_name"])
    return findings
