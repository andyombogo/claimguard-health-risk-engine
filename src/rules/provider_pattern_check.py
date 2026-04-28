"""Provider-level pattern validation rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig
from src.rules._shared import (
    flag_rows_to_findings,
    initialize_rule_output,
    normalize_claims_dataframe,
)
from src.rules.duplicate_claims import flag_exact_duplicates, flag_near_duplicates

RULE_NAME = "provider_pattern_risk"
_REQUIRED_COLUMNS = ["claim_id", "provider_id", "claim_amount"]


def compute_provider_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate provider-level usage and billing metrics for risk review."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, RULE_NAME)
    working_df = normalized_df.copy()

    high_value_threshold = working_df["claim_amount"].quantile(0.90)
    exact_duplicate_flags = flag_exact_duplicates(working_df)
    near_duplicate_flags = flag_near_duplicates(working_df)
    duplicate_claim_ids = set(
        pd.concat([exact_duplicate_flags, near_duplicate_flags], ignore_index=True)
        .loc[lambda frame: frame["flag_status"], "claim_id"]
        .astype(str)
        .tolist()
    )
    working_df["duplicate_flag"] = working_df["claim_id"].astype(str).isin(duplicate_claim_ids)
    working_df["high_value_flag"] = working_df["claim_amount"] >= high_value_threshold

    summary_df = (
        working_df.groupby("provider_id", dropna=False)
        .agg(
            total_claims=("claim_id", "count"),
            average_claim_amount=("claim_amount", "mean"),
            high_value_claim_rate=("high_value_flag", "mean"),
            duplicate_flag_rate=("duplicate_flag", "mean"),
        )
        .reset_index()
    )

    return summary_df


def flag_provider_pattern_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Flag claims tied to providers with unusually elevated utilization patterns."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, RULE_NAME)
    output_df = initialize_rule_output(normalized_df, RULE_NAME)
    provider_summary_df = compute_provider_risk_summary(normalized_df)

    total_claims_threshold = provider_summary_df["total_claims"].quantile(0.90)
    average_amount_threshold = provider_summary_df["average_claim_amount"].quantile(0.90)
    high_value_rate_threshold = provider_summary_df["high_value_claim_rate"].quantile(0.85)
    duplicate_rate_threshold = provider_summary_df["duplicate_flag_rate"].quantile(0.85)

    flagged_provider_ids: dict[str, tuple[str, str]] = {}
    for _, provider_row in provider_summary_df.iterrows():
        signals: list[str] = []
        if provider_row["total_claims"] >= total_claims_threshold:
            signals.append(
                f"total claims {int(provider_row['total_claims'])} are elevated"
            )
        if provider_row["average_claim_amount"] >= average_amount_threshold:
            signals.append(
                f"average claim amount {provider_row['average_claim_amount']:,.2f} is elevated"
            )
        if provider_row["high_value_claim_rate"] >= high_value_rate_threshold and provider_row[
            "high_value_claim_rate"
        ] > 0:
            signals.append(
                f"high-value claim rate {provider_row['high_value_claim_rate']:.0%} is elevated"
            )
        if provider_row["duplicate_flag_rate"] >= duplicate_rate_threshold and provider_row[
            "duplicate_flag_rate"
        ] > 0:
            signals.append(
                f"duplicate-linked claim rate {provider_row['duplicate_flag_rate']:.0%} is elevated"
            )

        provider_flagged = (
            provider_row["total_claims"] >= total_claims_threshold
            and provider_row["average_claim_amount"] >= average_amount_threshold
        ) or len(signals) >= 3

        if not provider_flagged:
            continue

        severity = "critical" if len(signals) >= 4 else "high"
        explanation = (
            "Provider-level pattern suggests additional review because "
            + "; ".join(signals)
            + "."
        )
        flagged_provider_ids[str(provider_row["provider_id"])] = (severity, explanation)

    if not flagged_provider_ids:
        return output_df

    provider_mask = normalized_df["provider_id"].astype(str).isin(flagged_provider_ids)
    output_df.loc[provider_mask, "flag_status"] = True
    output_df.loc[provider_mask, "points"] = 15
    output_df.loc[provider_mask, "severity"] = normalized_df.loc[provider_mask, "provider_id"].map(
        lambda provider_id: flagged_provider_ids[str(provider_id)][0]
    )
    output_df.loc[provider_mask, "explanation"] = normalized_df.loc[provider_mask, "provider_id"].map(
        lambda provider_id: flagged_provider_ids[str(provider_id)][1]
    )

    return output_df


def evaluate_provider_pattern_check(
    claim_row: pd.Series,
    claims_df: pd.DataFrame | RiskRulesConfig | None = None,
    rules_config: RiskRulesConfig | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns provider-pattern findings for one claim."""

    if isinstance(claims_df, RiskRulesConfig):
        rules_config = claims_df
        claims_df = None

    if isinstance(claims_df, pd.DataFrame):
        rule_output_df = flag_provider_pattern_risk(claims_df)
        claim_id = str(claim_row.get("claim_id", ""))
        claim_findings_df = rule_output_df.loc[
            (rule_output_df["claim_id"] == claim_id) & (rule_output_df["flag_status"])
        ]
        return flag_rows_to_findings(claim_findings_df)

    findings: list[dict[str, Any]] = []
    provider_count = float(
        claim_row.get("same_provider_claim_count_30d", claim_row.get("provider_claims_90d", 0))
        or 0
    )
    member_count = float(
        claim_row.get("previous_claim_count_90d", claim_row.get("member_claims_180d", 0))
        or 0
    )

    provider_threshold = 40
    member_threshold = 6
    if rules_config is not None:
        if "provider_history_volume" in rules_config.rules:
            provider_threshold = rules_config.rules["provider_history_volume"].parameters.get(
                "provider_claims_90d_threshold",
                provider_threshold,
            )
        if "member_repeat_usage" in rules_config.rules:
            member_threshold = rules_config.rules["member_repeat_usage"].parameters.get(
                "member_claims_180d_threshold",
                member_threshold,
            )

    if provider_count >= provider_threshold:
        findings.append(
            {
                "rule_name": "provider_history_volume",
                "weight": 12,
                "reason": "Provider recent claim volume exceeds the configured review threshold.",
                "severity": "medium",
            }
        )
    if member_count >= member_threshold:
        findings.append(
            {
                "rule_name": "member_repeat_usage",
                "weight": 10,
                "reason": "Member recent utilization exceeds the configured review threshold.",
                "severity": "medium",
            }
        )

    return findings
