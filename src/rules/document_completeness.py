"""Document completeness validation rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig
from src.rules._shared import (
    flag_rows_to_findings,
    initialize_rule_output,
    normalize_claims_dataframe,
)

RULE_NAME = "missing_documents"
_REQUIRED_COLUMNS = [
    "claim_id",
    "has_invoice",
    "has_discharge_summary",
    "has_lab_report",
]


def flag_missing_documents(df: pd.DataFrame) -> pd.DataFrame:
    """Flag claims that are missing one or more required document checks."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, RULE_NAME)
    output_df = initialize_rule_output(normalized_df, RULE_NAME)

    missing_documents_by_row: list[list[str]] = []
    for _, row in normalized_df.iterrows():
        missing_documents: list[str] = []
        if not bool(row["has_invoice"]):
            missing_documents.append("invoice")
        if not bool(row["has_discharge_summary"]):
            missing_documents.append("discharge summary")
        if not bool(row["has_lab_report"]):
            missing_documents.append("lab report")
        missing_documents_by_row.append(missing_documents)

    missing_counts = pd.Series([len(items) for items in missing_documents_by_row], index=output_df.index)
    flagged_mask = missing_counts > 0

    points_lookup = {1: 5, 2: 10, 3: 15}
    severity_lookup = {1: "low", 2: "medium", 3: "high"}

    output_df.loc[flagged_mask, "flag_status"] = True
    output_df.loc[flagged_mask, "points"] = missing_counts.loc[flagged_mask].map(points_lookup)
    output_df.loc[flagged_mask, "severity"] = missing_counts.loc[flagged_mask].map(severity_lookup)
    output_df.loc[flagged_mask, "explanation"] = [
        "Missing required document(s): " + ", ".join(missing_documents) + "."
        for missing_documents in pd.Series(missing_documents_by_row, index=output_df.index).loc[flagged_mask]
    ]

    return output_df


def evaluate_document_completeness(
    claim_row: pd.Series,
    claims_df: pd.DataFrame | RiskRulesConfig | None = None,
    rules_config: RiskRulesConfig | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns document findings for one claim."""

    if isinstance(claims_df, RiskRulesConfig):
        rules_config = claims_df
        claims_df = None

    if isinstance(claims_df, pd.DataFrame):
        rule_output_df = flag_missing_documents(claims_df)
        claim_id = str(claim_row.get("claim_id", ""))
        claim_findings_df = rule_output_df.loc[
            (rule_output_df["claim_id"] == claim_id) & (rule_output_df["flag_status"])
        ]
        return flag_rows_to_findings(claim_findings_df)

    document_status = str(claim_row.get("document_status", "")).strip().lower()
    if document_status == "partial":
        return [
            {
                "rule_name": RULE_NAME,
                "weight": 10,
                "reason": "Supporting documents are incomplete and require verification.",
                "severity": "medium",
            }
        ]
    if document_status == "missing_discharge_summary":
        return [
            {
                "rule_name": RULE_NAME,
                "weight": 5,
                "reason": "The discharge summary is missing and requires follow-up.",
                "severity": "low",
            }
        ]

    return []
