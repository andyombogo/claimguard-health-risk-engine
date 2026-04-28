"""Maker-checker workflow metadata helpers."""

from __future__ import annotations

import pandas as pd

from src.config.settings import get_settings


def assign_maker_checker(scored_claims_df: pd.DataFrame) -> pd.DataFrame:
    """Attach simple maker-checker workflow columns to scored claims."""

    settings = get_settings()
    workflow_df = scored_claims_df.copy()
    workflow_df["maker_owner"] = settings.default_maker
    workflow_df["checker_required"] = workflow_df["risk_band"].isin(
        ["High Risk", "Critical Risk"]
    )
    workflow_df["checker_owner"] = workflow_df["checker_required"].map(
        lambda required: settings.default_checker if required else ""
    )
    workflow_df["maker_status"] = "Pending"
    workflow_df["checker_status"] = workflow_df["checker_required"].map(
        lambda required: "Pending" if required else "Not required"
    )
    return workflow_df
