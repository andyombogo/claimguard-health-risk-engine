"""Triage queue assembly for reviewer-facing outputs."""

from __future__ import annotations

import pandas as pd

from src.scoring.risk_score import score_claims


def build_triage_queue(
    claims_df: pd.DataFrame,
    scored_claims_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Merge source claims with scores and sort into review priority order."""

    scored_df = scored_claims_df if scored_claims_df is not None else score_claims(claims_df)
    queue_df = claims_df.merge(scored_df, on="claim_id", how="left")

    amount_column = "claimed_amount" if "claimed_amount" in queue_df.columns else "claim_amount"
    sort_columns = ["requires_escalation", "risk_score", amount_column]
    ascending = [False, False, False]
    return queue_df.sort_values(sort_columns, ascending=ascending).reset_index(drop=True)
