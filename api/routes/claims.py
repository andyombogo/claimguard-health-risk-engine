"""Claims-related API routes and synthetic demo data helpers."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from src.rules.run_all_rules import run_all_rules
from src.scoring.explainability import build_claim_risk_profile, generate_claim_explanation
from src.scoring.risk_score import score_claims
from src.utils.helpers import repo_root
from src.workflow.triage_queue import build_triage_queue

router = APIRouter(prefix="/claims", tags=["claims"])

DEMO_CLAIMS_PATH = repo_root() / "data" / "synthetic" / "synthetic_health_claims.csv"
MISSING_DATA_DETAIL = (
    "Synthetic demo claims were not found. Run "
    "`py -B src\\data_processing\\generate_synthetic_claims.py` from the repository root first."
)


@lru_cache(maxsize=1)
def _cached_demo_claims() -> pd.DataFrame:
    """Load the synthetic demo dataset once for API reads."""

    if not DEMO_CLAIMS_PATH.exists():
        raise FileNotFoundError(MISSING_DATA_DETAIL)
    return pd.read_csv(DEMO_CLAIMS_PATH)


def load_demo_claims_frame() -> pd.DataFrame:
    """Return a copy of the synthetic demo claims for route handlers."""

    try:
        return _cached_demo_claims().copy()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def get_demo_scoring_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return claims, flags, scored claims, and queue views for the demo API."""

    claims_df = load_demo_claims_frame()
    flags_df = run_all_rules(claims_df)
    scored_df = score_claims(claims_df, flags_df)
    queue_df = build_triage_queue(claims_df, scored_df)
    return claims_df, flags_df, scored_df, queue_df


@router.get("/raw")
def get_raw_claims() -> dict[str, object]:
    """Return the synthetic raw claims used by the prototype."""

    claims_df = load_demo_claims_frame()
    return {
        "record_count": int(len(claims_df)),
        "claims": jsonable_encoder(claims_df.to_dict(orient="records")),
    }


@router.get("/scored")
def get_scored_claims() -> dict[str, object]:
    """Return claims merged with their current rule-based risk scores."""

    claims_df, _, scored_df, _ = get_demo_scoring_frames()
    merged_df = claims_df.merge(scored_df, on="claim_id", how="left")
    return {
        "record_count": int(len(merged_df)),
        "claims": jsonable_encoder(merged_df.to_dict(orient="records")),
    }


@router.get("/queue")
def get_claim_queue() -> dict[str, object]:
    """Return the review queue view for the synthetic claims portfolio."""

    _, _, _, queue_df = get_demo_scoring_frames()
    return {
        "record_count": int(len(queue_df)),
        "claims": jsonable_encoder(queue_df.to_dict(orient="records")),
    }


@router.get("/{claim_id}")
def get_claim_detail(claim_id: str) -> dict[str, object]:
    """Return a scored claim detail payload for API demos."""

    claims_df, flags_df, _, _ = get_demo_scoring_frames()
    claim_mask = claims_df["claim_id"].astype(str) == str(claim_id)
    if not claim_mask.any():
        raise HTTPException(status_code=404, detail=f"Claim ID {claim_id} was not found.")

    claim_flags_df = flags_df.loc[flags_df["claim_id"].astype(str) == str(claim_id)].copy()
    risk_profile = build_claim_risk_profile(claims_df, flags_df, claim_id)
    return jsonable_encoder(
        {
            "claim_id": claim_id,
            "claim": claims_df.loc[claim_mask].iloc[0].to_dict(),
            "risk_profile": risk_profile,
            "flags": claim_flags_df.to_dict(orient="records"),
            "explanation": generate_claim_explanation(claim_id, flags_df),
        }
    )
