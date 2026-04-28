"""Related-claim context helpers for reviewer-facing claim profiles."""

from __future__ import annotations

import pandas as pd

RELATED_CLAIM_COLUMNS = [
    "claim_id",
    "claim_date",
    "provider_name",
    "diagnosis_description",
    "claim_amount",
    "total_risk_score",
    "risk_band",
    "relationship_hint",
    "days_from_selected_claim",
    "amount_difference_pct",
]


def _as_datetime(series: pd.Series) -> pd.Series:
    """Convert a series to datetimes without raising on malformed values."""

    return pd.to_datetime(series, errors="coerce")


def _amount_difference_pct(selected_amount: float, candidate_amount: float) -> float:
    """Return absolute amount difference as a percentage of the larger amount."""

    denominator = max(abs(float(selected_amount or 0)), abs(float(candidate_amount or 0)), 1.0)
    return round(abs(float(selected_amount or 0) - float(candidate_amount or 0)) / denominator * 100, 2)


def _column_equals(frame: pd.DataFrame, column: str, value: object) -> pd.Series:
    """Return a boolean series for equality checks, even when a column is absent."""

    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column] == value


def find_related_claims(
    claims_df: pd.DataFrame,
    claim_id: str,
    date_window_days: int = 14,
    amount_tolerance: float = 0.05,
    member_history_days: int = 90,
    provider_history_days: int = 30,
    limit: int = 12,
) -> pd.DataFrame:
    """Find reviewer-friendly related claims for a selected claim.

    Related claims are context for review. They are not treated as confirmed
    duplicates unless they satisfy the near-duplicate criteria.
    """

    if "claim_id" not in claims_df.columns or claims_df.empty:
        return pd.DataFrame(columns=RELATED_CLAIM_COLUMNS)

    working_df = claims_df.copy()
    working_df["claim_id"] = working_df["claim_id"].astype(str)
    selected_df = working_df.loc[working_df["claim_id"] == str(claim_id)]
    if selected_df.empty:
        return pd.DataFrame(columns=RELATED_CLAIM_COLUMNS)

    selected_row = selected_df.iloc[0]
    candidates_df = working_df.loc[working_df["claim_id"] != str(claim_id)].copy()
    if candidates_df.empty:
        return pd.DataFrame(columns=RELATED_CLAIM_COLUMNS)

    selected_date = pd.to_datetime(selected_row.get("claim_date"), errors="coerce")
    candidates_df["claim_date"] = _as_datetime(candidates_df.get("claim_date", pd.Series(dtype=object)))
    if pd.isna(selected_date):
        candidates_df["days_from_selected_claim"] = pd.NA
    else:
        candidates_df["days_from_selected_claim"] = (
            candidates_df["claim_date"] - selected_date
        ).dt.days.abs()

    if "claim_amount" not in candidates_df.columns:
        candidates_df["claim_amount"] = 0
    candidates_df["claim_amount"] = pd.to_numeric(candidates_df["claim_amount"], errors="coerce").fillna(0)

    selected_amount = float(selected_row.get("claim_amount", 0) or 0)
    candidates_df["amount_difference_pct"] = candidates_df["claim_amount"].apply(
        lambda value: _amount_difference_pct(selected_amount, float(value or 0))
    )

    same_member = _column_equals(candidates_df, "member_id", selected_row.get("member_id"))
    same_provider = _column_equals(candidates_df, "provider_id", selected_row.get("provider_id"))
    same_diagnosis = _column_equals(candidates_df, "diagnosis_code", selected_row.get("diagnosis_code"))
    same_procedure = _column_equals(candidates_df, "procedure_code", selected_row.get("procedure_code"))
    close_date = candidates_df["days_from_selected_claim"].le(date_window_days).fillna(False)
    member_history = candidates_df["days_from_selected_claim"].le(member_history_days).fillna(False)
    provider_history = candidates_df["days_from_selected_claim"].le(provider_history_days).fillna(False)
    similar_amount = candidates_df["amount_difference_pct"].le(amount_tolerance * 100)

    near_duplicate = same_member & same_provider & same_diagnosis & same_procedure & close_date & similar_amount
    same_member_context = same_member & member_history
    same_provider_diagnosis_context = same_provider & same_diagnosis & provider_history

    related_mask = near_duplicate | same_member_context | same_provider_diagnosis_context
    related_df = candidates_df.loc[related_mask].copy()
    if related_df.empty:
        return pd.DataFrame(columns=RELATED_CLAIM_COLUMNS)

    def relationship_hint(row: pd.Series) -> str:
        is_near_duplicate = bool(near_duplicate.loc[row.name])
        if is_near_duplicate:
            return "Near-duplicate review context"
        if row.get("member_id") == selected_row.get("member_id"):
            return "Same member recent history"
        return "Same provider and diagnosis"

    related_df["relationship_hint"] = related_df.apply(relationship_hint, axis=1)
    related_df["relationship_rank"] = related_df["relationship_hint"].map(
        {
            "Near-duplicate review context": 0,
            "Same member recent history": 1,
            "Same provider and diagnosis": 2,
        }
    )

    for column in RELATED_CLAIM_COLUMNS:
        if column not in related_df.columns:
            related_df[column] = ""

    related_df = related_df.sort_values(
        ["relationship_rank", "total_risk_score", "days_from_selected_claim"],
        ascending=[True, False, True],
    )
    related_df["claim_date"] = related_df["claim_date"].dt.strftime("%Y-%m-%d").fillna("")
    return related_df[RELATED_CLAIM_COLUMNS].head(limit).reset_index(drop=True)
