"""Claim-level risk scoring built from transparent rule outputs."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.rules.run_all_rules import run_all_rules
from src.scoring.explainability import generate_claim_explanation
from src.scoring.risk_band import assign_recommended_action, assign_risk_band

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _ensure_claim_id_column(df: pd.DataFrame, dataframe_name: str) -> None:
    """Validate that the required claim identifier column exists."""

    if "claim_id" not in df.columns:
        raise ValueError(f"{dataframe_name} must contain a claim_id column.")


def _highest_severity(severities: pd.Series) -> str:
    """Return the most severe label in a series of severity values."""

    normalized_values = (
        severities.fillna("none").astype(str).str.strip().str.lower().tolist()
    )
    if not normalized_values:
        return "none"
    return max(normalized_values, key=lambda value: SEVERITY_ORDER.get(value, 0))


def _aggregate_triggered_rules(claim_flags_df: pd.DataFrame) -> str:
    """Serialize unique triggered rule names for compatibility outputs."""

    if claim_flags_df.empty:
        return "none"
    return "|".join(claim_flags_df["rule_name"].drop_duplicates().astype(str).tolist())


def calculate_risk_scores(claims_df: pd.DataFrame, flags_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate long-format rule flags into claim-level risk scores.

    Example output shape:

    ```text
    claim_id     total_risk_score risk_band      number_of_flags highest_severity recommended_action
    CLM-000101   55               High Risk     3               high             Maker-checker review required
    ```
    """

    _ensure_claim_id_column(claims_df, "claims_df")
    _ensure_claim_id_column(flags_df, "flags_df")

    claim_ids_df = claims_df[["claim_id"]].copy()
    claim_ids_df["claim_id"] = claim_ids_df["claim_id"].astype(str)

    working_flags_df = flags_df.copy()
    working_flags_df["claim_id"] = working_flags_df["claim_id"].astype(str)
    if "flag_status" in working_flags_df.columns:
        working_flags_df = working_flags_df.loc[working_flags_df["flag_status"]].copy()

    if working_flags_df.empty:
        scored_df = claim_ids_df.copy()
        scored_df["total_risk_score"] = 0
        scored_df["risk_band"] = "Low Risk"
        scored_df["number_of_flags"] = 0
        scored_df["highest_severity"] = "none"
        scored_df["recommended_action"] = assign_recommended_action("Low Risk")
        return scored_df

    aggregated_df = (
        working_flags_df.groupby("claim_id", as_index=False)
        .agg(
            total_risk_score=("points", "sum"),
            number_of_flags=("rule_name", "count"),
            highest_severity=("severity", _highest_severity),
        )
    )
    aggregated_df["total_risk_score"] = aggregated_df["total_risk_score"].clip(upper=100).astype(int)
    aggregated_df["risk_band"] = aggregated_df["total_risk_score"].apply(assign_risk_band)
    aggregated_df["recommended_action"] = aggregated_df["risk_band"].apply(assign_recommended_action)

    scored_df = claim_ids_df.merge(aggregated_df, on="claim_id", how="left")
    scored_df["total_risk_score"] = scored_df["total_risk_score"].fillna(0).astype(int)
    scored_df["number_of_flags"] = scored_df["number_of_flags"].fillna(0).astype(int)
    scored_df["highest_severity"] = scored_df["highest_severity"].fillna("none")
    scored_df["risk_band"] = scored_df["total_risk_score"].apply(assign_risk_band)
    scored_df["recommended_action"] = scored_df["risk_band"].apply(assign_recommended_action)
    return scored_df


def score_single_claim(
    claim_row: pd.Series | dict[str, Any],
    claims_df: pd.DataFrame,
    rules_config: object | None = None,
) -> dict[str, Any]:
    """Return a compatibility score payload for a single claim."""

    row_df = pd.DataFrame([dict(claim_row) if isinstance(claim_row, dict) else claim_row.to_dict()])
    combined_claims_df = claims_df.copy()
    flags_df = run_all_rules(combined_claims_df)
    scored_df = calculate_risk_scores(combined_claims_df, flags_df).set_index("claim_id")

    claim_id = str(row_df.iloc[0]["claim_id"])
    claim_flags_df = flags_df.loc[flags_df["claim_id"].astype(str) == claim_id].copy()
    claim_score = scored_df.loc[claim_id]

    return {
        "claim_id": claim_id,
        "risk_score": int(claim_score["total_risk_score"]),
        "total_risk_score": int(claim_score["total_risk_score"]),
        "risk_band": str(claim_score["risk_band"]),
        "number_of_flags": int(claim_score["number_of_flags"]),
        "rule_count": int(claim_score["number_of_flags"]),
        "highest_severity": str(claim_score["highest_severity"]),
        "recommended_action": str(claim_score["recommended_action"]),
        "review_action": str(claim_score["recommended_action"]),
        "triggered_rules": _aggregate_triggered_rules(claim_flags_df),
        "requires_escalation": str(claim_score["risk_band"]) in {"High Risk", "Critical Risk"},
        "explanation_summary": generate_claim_explanation(claim_id, flags_df),
    }


def score_claims(
    claims_df: pd.DataFrame,
    flags_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Score every claim using the long-format rule engine and expose compatibility columns."""

    _ensure_claim_id_column(claims_df, "claims_df")
    resolved_flags_df = flags_df if flags_df is not None else run_all_rules(claims_df)
    scored_df = calculate_risk_scores(claims_df, resolved_flags_df)

    flags_working_df = resolved_flags_df.copy()
    flags_working_df["claim_id"] = flags_working_df["claim_id"].astype(str)
    explanation_lookup = {
        claim_id: generate_claim_explanation(claim_id, flags_working_df)
        for claim_id in scored_df["claim_id"].astype(str).tolist()
    }
    triggered_rules_lookup = {
        claim_id: _aggregate_triggered_rules(
            flags_working_df.loc[flags_working_df["claim_id"] == claim_id]
        )
        for claim_id in scored_df["claim_id"].astype(str).tolist()
    }

    compatibility_df = scored_df.copy()
    compatibility_df["risk_score"] = compatibility_df["total_risk_score"]
    compatibility_df["review_action"] = compatibility_df["recommended_action"]
    compatibility_df["rule_count"] = compatibility_df["number_of_flags"]
    compatibility_df["requires_escalation"] = compatibility_df["risk_band"].isin(
        ["High Risk", "Critical Risk"]
    )
    compatibility_df["triggered_rules"] = compatibility_df["claim_id"].map(triggered_rules_lookup)
    compatibility_df["explanation_summary"] = compatibility_df["claim_id"].map(explanation_lookup)
    return compatibility_df
