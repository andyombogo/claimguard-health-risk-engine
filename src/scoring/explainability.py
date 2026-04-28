"""Explainability helpers for claim-level risk outputs."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from src.config.settings import load_risk_rules_config
from src.scoring.risk_band import assign_recommended_action, assign_risk_band

_RULE_LABEL_OVERRIDES = {
    "exact_duplicate_claim": "exact duplicate claim",
    "near_duplicate_claim": "near duplicate claim",
    "abnormal_billing": "abnormal billing",
    "diagnosis_treatment_mismatch": "diagnosis-treatment mismatch",
    "provider_pattern_risk": "provider pattern risk",
    "missing_documents": "missing documents",
}

_SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


@lru_cache(maxsize=1)
def _rule_description_lookup() -> dict[str, str]:
    """Load rule descriptions from configuration for explainability use."""

    config = load_risk_rules_config()
    return {rule_name: rule.description for rule_name, rule in config.rules.items()}


def humanize_rule_name(rule_name: str) -> str:
    """Convert a technical rule name into a reviewer-friendly label."""

    if rule_name in _RULE_LABEL_OVERRIDES:
        return _RULE_LABEL_OVERRIDES[rule_name]

    description = _rule_description_lookup().get(rule_name)
    if description:
        return description[0].lower() + description[1:]

    return rule_name.replace("_", " ")


def _join_human_labels(labels: list[str]) -> str:
    """Join human-readable labels into a concise list phrase."""

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"


def generate_claim_explanation(claim_id: str, flags_df: pd.DataFrame) -> str:
    """Build a concise risk explanation for one claim from the rule flags."""

    claim_flags_df = flags_df.loc[
        (flags_df["claim_id"].astype(str) == str(claim_id)) & (flags_df["flag_status"])
    ].copy()

    if claim_flags_df.empty:
        return (
            f"Claim {claim_id} is low risk because no review flags were triggered in the "
            "current rule set."
        )

    total_points = int(claim_flags_df["points"].sum())
    risk_band = assign_risk_band(total_points)
    unique_rule_labels = [
        humanize_rule_name(rule_name)
        for rule_name in claim_flags_df["rule_name"].drop_duplicates().tolist()
    ]
    flag_count = len(claim_flags_df)

    return (
        f"Claim {claim_id} is {risk_band.lower()} because it has {flag_count} review "
        f"flag{'s' if flag_count != 1 else ''}: {_join_human_labels(unique_rule_labels)}."
    )


def build_claim_risk_profile(
    claims_df: pd.DataFrame,
    flags_df: pd.DataFrame,
    claim_id: str,
) -> dict[str, Any]:
    """Return a review-oriented risk profile for a single claim."""

    if "claim_id" not in claims_df.columns:
        raise ValueError("claims_df must contain a claim_id column.")

    claim_matches = claims_df.loc[claims_df["claim_id"].astype(str) == str(claim_id)]
    if claim_matches.empty:
        raise ValueError(f"Claim ID {claim_id} was not found in claims_df.")

    claim_summary = claim_matches.iloc[0].to_dict()
    claim_flags_df = flags_df.loc[
        (flags_df["claim_id"].astype(str) == str(claim_id)) & (flags_df["flag_status"])
    ].copy()

    total_score = int(claim_flags_df["points"].sum()) if not claim_flags_df.empty else 0
    risk_band = assign_risk_band(total_score)
    recommended_action = assign_recommended_action(risk_band)
    highest_severity = "none"
    if not claim_flags_df.empty:
        severity_values = (
            claim_flags_df["severity"].fillna("none").astype(str).str.lower().tolist()
        )
        highest_severity = max(
            severity_values,
            key=lambda value: _SEVERITY_ORDER.get(value, 0),
        )

    flagged_rules = [
        {
            "rule_name": row["rule_name"],
            "rule_label": humanize_rule_name(str(row["rule_name"])),
            "severity": row["severity"],
            "points": int(row["points"]),
        }
        for _, row in claim_flags_df.iterrows()
    ]
    explanations = claim_flags_df["explanation"].astype(str).tolist()

    reviewer_note_template = (
        f"Reviewer note template for {claim_id}:\n"
        f"- Risk band: {risk_band}\n"
        f"- Recommended action: {recommended_action}\n"
        f"- Highest severity observed: {highest_severity}\n"
        "- Verification completed:\n"
        "- Supporting evidence reviewed:\n"
        "- Follow-up decision:\n"
        "- Additional comments:"
    )

    return {
        "claim_summary": claim_summary,
        "risk_score": total_score,
        "risk_band": risk_band,
        "recommended_action": recommended_action,
        "flagged_rules": flagged_rules,
        "explanations": explanations,
        "reviewer_note_template": reviewer_note_template,
    }
