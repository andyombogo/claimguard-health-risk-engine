"""Dataframe schema validation for synthetic claims inputs."""

from __future__ import annotations

import pandas as pd

REQUIRED_CLAIM_COLUMNS = {
    "claim_id",
    "member_id",
    "provider_id",
    "claim_type",
    "date_of_service",
    "diagnosis_code",
    "treatment_code",
    "claimed_amount",
    "document_status",
    "provider_claims_90d",
    "member_claims_180d",
    "escalation_trigger",
}


def validate_claims_dataframe(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the minimum required schema is present."""

    missing_columns = REQUIRED_CLAIM_COLUMNS.difference(claims_df.columns)
    if missing_columns:
        missing_display = ", ".join(sorted(missing_columns))
        raise ValueError(f"Claims dataframe is missing required columns: {missing_display}")

    return claims_df
