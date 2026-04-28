"""Provider intelligence API routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from api.routes.claims import get_demo_scoring_frames

router = APIRouter(prefix="/providers", tags=["providers"])

PROVIDER_NOTE = (
    "Provider-level patterns are screening indicators and should be interpreted with context."
)


@router.get("/intelligence")
def provider_intelligence() -> dict[str, object]:
    """Return provider-level summary metrics derived from the synthetic portfolio."""

    claims_df, _, scored_df, _ = get_demo_scoring_frames()
    provider_df = claims_df.merge(scored_df, on="claim_id", how="left")

    summary_df = (
        provider_df.groupby(["provider_id", "provider_name"], dropna=False)
        .agg(
            total_claims=("claim_id", "count"),
            average_claim_amount=("claim_amount", "mean"),
            high_risk_claims=("risk_band", lambda series: int(series.isin(["High Risk", "Critical Risk"]).sum())),
            critical_risk_claims=("risk_band", lambda series: int((series == "Critical Risk").sum())),
            percentage_flagged=("number_of_flags", lambda series: round(float(series.gt(0).mean() * 100), 2)),
        )
        .reset_index()
        .sort_values(["high_risk_claims", "total_claims", "average_claim_amount"], ascending=[False, False, False])
    )
    summary_df["average_claim_amount"] = summary_df["average_claim_amount"].round(2)

    return {
        "note": PROVIDER_NOTE,
        "provider_count": int(len(summary_df)),
        "providers": jsonable_encoder(summary_df.to_dict(orient="records")),
    }
