"""Feature engineering helpers for the prototype rule engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_processing.clean_claims import clean_claims_dataframe
from src.data_processing.validate_schema import validate_claims_dataframe


def build_claim_features(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Create lightweight derived features used by rule evaluation."""

    validated_df = validate_claims_dataframe(claims_df.copy())
    featured_df = clean_claims_dataframe(validated_df)

    for column_name in ("claimed_amount", "approved_amount"):
        if column_name in featured_df.columns:
            featured_df[column_name] = pd.to_numeric(
                featured_df[column_name],
                errors="coerce",
            ).fillna(0)

    for column_name in ("provider_claims_90d", "member_claims_180d"):
        featured_df[column_name] = pd.to_numeric(
            featured_df[column_name],
            errors="coerce",
        ).fillna(0)

    featured_df["length_of_stay_days"] = (
        featured_df["discharge_date"] - featured_df["admission_date"]
    ).dt.days.fillna(0)
    featured_df["length_of_stay_days"] = featured_df["length_of_stay_days"].clip(lower=0)

    denominator = np.where(featured_df["length_of_stay_days"] > 0, featured_df["length_of_stay_days"], 1)
    featured_df["amount_per_day"] = featured_df["claimed_amount"] / denominator
    featured_df["claim_signature"] = (
        featured_df["member_id"].fillna("")
        + "|"
        + featured_df["provider_id"].fillna("")
        + "|"
        + featured_df["treatment_code"].fillna("")
    )

    return featured_df
