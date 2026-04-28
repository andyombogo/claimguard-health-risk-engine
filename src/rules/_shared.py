"""Shared helpers for explainable rule-based claim validation."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

RULE_OUTPUT_COLUMNS = [
    "claim_id",
    "rule_name",
    "flag_status",
    "severity",
    "points",
    "explanation",
]

_COLUMN_ALIASES: dict[str, list[str]] = {
    "claim_id": ["claim_id"],
    "member_id": ["member_id"],
    "provider_id": ["provider_id"],
    "diagnosis_code": ["diagnosis_code"],
    "procedure_code": ["procedure_code", "treatment_code"],
    "claim_amount": ["claim_amount", "claimed_amount"],
    "claim_date": ["claim_date", "date_of_service"],
    "provider_type": ["provider_type"],
    "document_status": ["document_status"],
    "has_invoice": ["has_invoice"],
    "has_discharge_summary": ["has_discharge_summary"],
    "has_lab_report": ["has_lab_report"],
    "previous_claim_count_90d": ["previous_claim_count_90d", "member_claims_180d"],
    "same_provider_claim_count_30d": ["same_provider_claim_count_30d", "provider_claims_90d"],
}


def _coerce_boolean_series(series: pd.Series) -> pd.Series:
    """Convert mixed boolean-like values to actual booleans."""

    truthy = {"true", "yes", "y", "1"}
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    return (
        series.fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(truthy)
    )


def _derive_document_flags(normalized_df: pd.DataFrame) -> pd.DataFrame:
    """Derive document flags when the dataset uses a compact document status field."""

    if {
        "has_invoice",
        "has_discharge_summary",
        "has_lab_report",
    }.issubset(normalized_df.columns):
        normalized_df["has_invoice"] = _coerce_boolean_series(normalized_df["has_invoice"])
        normalized_df["has_discharge_summary"] = _coerce_boolean_series(
            normalized_df["has_discharge_summary"]
        )
        normalized_df["has_lab_report"] = _coerce_boolean_series(normalized_df["has_lab_report"])
        return normalized_df

    if "document_status" not in normalized_df.columns:
        return normalized_df

    status = normalized_df["document_status"].fillna("").astype(str).str.strip().str.lower()
    normalized_df["has_invoice"] = ~status.isin({"missing_invoice"})
    normalized_df["has_discharge_summary"] = ~status.isin(
        {"missing_discharge_summary", "partial"}
    )
    normalized_df["has_lab_report"] = ~status.isin({"missing_lab_report", "partial"})
    return normalized_df


def normalize_claims_dataframe(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    rule_name: str,
) -> pd.DataFrame:
    """Normalize supported schema variants to a canonical claims dataframe."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{rule_name} expects a pandas DataFrame input.")

    normalized_df = df.copy()
    rename_map: dict[str, str] = {}

    for canonical_name, aliases in _COLUMN_ALIASES.items():
        if canonical_name in normalized_df.columns:
            continue
        for alias in aliases:
            if alias in normalized_df.columns:
                rename_map[alias] = canonical_name
                break

    normalized_df = normalized_df.rename(columns=rename_map)
    normalized_df = _derive_document_flags(normalized_df)

    missing_columns = [column for column in required_columns if column not in normalized_df.columns]
    if missing_columns:
        missing_display = ", ".join(sorted(missing_columns))
        raise ValueError(f"{rule_name} requires columns: {missing_display}")

    if "claim_id" in normalized_df.columns:
        normalized_df["claim_id"] = normalized_df["claim_id"].astype(str)

    if "claim_date" in normalized_df.columns:
        normalized_df["claim_date"] = pd.to_datetime(
            normalized_df["claim_date"],
            errors="coerce",
        )

    for numeric_column in [
        "claim_amount",
        "approved_amount",
        "previous_claim_count_90d",
        "same_provider_claim_count_30d",
    ]:
        if numeric_column in normalized_df.columns:
            normalized_df[numeric_column] = pd.to_numeric(
                normalized_df[numeric_column],
                errors="coerce",
            )

    return normalized_df


def initialize_rule_output(df: pd.DataFrame, rule_name: str) -> pd.DataFrame:
    """Create a standardized rule output frame aligned to the input claim IDs."""

    return pd.DataFrame(
        {
            "claim_id": df["claim_id"].astype(str),
            "rule_name": rule_name,
            "flag_status": False,
            "severity": pd.Series([pd.NA] * len(df), dtype="object"),
            "points": 0,
            "explanation": "",
        }
    )


def flag_rows_to_findings(rule_output_df: pd.DataFrame) -> list[dict[str, object]]:
    """Convert standardized rule output rows to legacy finding dictionaries."""

    flagged_rows = rule_output_df.loc[rule_output_df["flag_status"]]
    return [
        {
            "rule_name": row["rule_name"],
            "weight": int(row["points"]),
            "reason": row["explanation"],
            "severity": row["severity"],
        }
        for _, row in flagged_rows.iterrows()
    ]


def similar_claim_text(claim_ids: Iterable[str]) -> str:
    """Format a list of claim IDs for reviewer-facing explanations."""

    unique_ids = sorted({str(claim_id) for claim_id in claim_ids if str(claim_id).strip()})
    if not unique_ids:
        return "none"
    return ", ".join(unique_ids)
