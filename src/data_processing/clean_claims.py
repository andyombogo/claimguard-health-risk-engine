"""Claim cleaning helpers for the synthetic prototype data."""

from __future__ import annotations

import pandas as pd

DATE_COLUMNS = ("date_of_service", "admission_date", "discharge_date")


def clean_claims_dataframe(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, blanks, and date fields."""

    cleaned_df = claims_df.copy()
    cleaned_df.columns = [column.strip().lower() for column in cleaned_df.columns]
    cleaned_df = cleaned_df.replace({"": pd.NA})

    for column_name in DATE_COLUMNS:
        if column_name in cleaned_df.columns:
            cleaned_df[column_name] = pd.to_datetime(
                cleaned_df[column_name],
                errors="coerce",
            )

    string_columns = cleaned_df.select_dtypes(include=["object"]).columns
    for column_name in string_columns:
        cleaned_df[column_name] = cleaned_df[column_name].astype("string").str.strip()

    return cleaned_df
