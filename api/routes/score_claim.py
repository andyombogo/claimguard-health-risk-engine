"""Single-claim scoring API route."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from api.routes.claims import load_demo_claims_frame
from api.schemas.claim_schema import ClaimInput
from src.rules._shared import RULE_OUTPUT_COLUMNS
from src.rules.abnormal_billing import flag_abnormal_billing
from src.rules.diagnosis_treatment_check import flag_diagnosis_treatment_mismatch
from src.rules.document_completeness import flag_missing_documents
from src.scoring.explainability import generate_claim_explanation
from src.scoring.risk_score import calculate_risk_scores

router = APIRouter(prefix="/score-claim", tags=["scoring"])

DISCLAIMER_TEXT = (
    "ClaimGuard scores are review-prioritization signals for human assessment only. "
    "They do not confirm fraud, wrongdoing, or final claim disposition."
)


def _empty_flags_df() -> pd.DataFrame:
    """Return an empty standardized flags dataframe."""

    return pd.DataFrame(columns=RULE_OUTPUT_COLUMNS)


@lru_cache(maxsize=1)
def _proxy_thresholds() -> tuple[int, int]:
    """Derive reasonable proxy thresholds from the synthetic demo portfolio when available."""

    try:
        reference_df = load_demo_claims_frame()
    except HTTPException:
        return 4, 3

    provider_threshold = max(
        int(
            pd.to_numeric(
                reference_df["same_provider_claim_count_30d"],
                errors="coerce",
            ).quantile(0.90)
            or 0
        ),
        4,
    )
    member_threshold = max(
        int(
            pd.to_numeric(
                reference_df["previous_claim_count_90d"],
                errors="coerce",
            ).quantile(0.90)
            or 0
        ),
        3,
    )
    return provider_threshold, member_threshold


def _flag_abnormal_billing_with_reference(claim_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Benchmark a single claim against the synthetic demo population when available."""

    try:
        reference_df = load_demo_claims_frame()
    except HTTPException:
        return _empty_flags_df(), False

    claim_id = str(claim_df.iloc[0]["claim_id"])
    reference_df = reference_df.loc[reference_df["claim_id"].astype(str) != claim_id].copy()
    combined_df = pd.concat([reference_df, claim_df], ignore_index=True, sort=False)
    abnormal_flags_df = flag_abnormal_billing(combined_df)
    return (
        abnormal_flags_df.loc[
            abnormal_flags_df["claim_id"].astype(str) == claim_id,
            RULE_OUTPUT_COLUMNS,
        ].copy(),
        True,
    )


def _flag_provider_proxy_risk(claim_df: pd.DataFrame) -> pd.DataFrame:
    """Create a provider-pattern flag using proxy history counts from the request."""

    claim_row = claim_df.iloc[0]
    claim_id = str(claim_row["claim_id"])
    provider_proxy_count = int(claim_row.get("same_provider_claim_count_30d", 0) or 0)
    member_proxy_count = int(claim_row.get("previous_claim_count_90d", 0) or 0)
    provider_threshold, member_threshold = _proxy_thresholds()

    if provider_proxy_count < provider_threshold and member_proxy_count < member_threshold:
        return _empty_flags_df()

    proxy_signals: list[str] = []
    if provider_proxy_count >= provider_threshold:
        proxy_signals.append(
            f"same-provider claim count in the last 30 days is {provider_proxy_count}"
        )
    if member_proxy_count >= member_threshold:
        proxy_signals.append(
            f"member claim count in the last 90 days is {member_proxy_count}"
        )

    severity = "high" if len(proxy_signals) == 2 or provider_proxy_count >= provider_threshold * 2 else "medium"
    explanation = (
        "Provider-pattern review is recommended because "
        + " and ".join(proxy_signals)
        + ". No detailed historical claim set was supplied with this request, so this flag is based on proxy context."
    )

    return pd.DataFrame(
        [
            {
                "claim_id": claim_id,
                "rule_name": "provider_pattern_risk",
                "flag_status": True,
                "severity": severity,
                "points": 15,
                "explanation": explanation,
            }
        ]
    )


def _combine_flag_frames(flag_frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine rule outputs into a flagged-only long-format dataframe."""

    populated_frames = [frame.copy() for frame in flag_frames if not frame.empty]
    if not populated_frames:
        return _empty_flags_df()

    combined_df = pd.concat(populated_frames, ignore_index=True, sort=False)
    combined_df = combined_df.loc[combined_df["flag_status"]].copy()
    if combined_df.empty:
        return _empty_flags_df()

    return combined_df[RULE_OUTPUT_COLUMNS].sort_values(
        by=["points", "rule_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def _build_limitation_note(claim_df: pd.DataFrame, used_reference_benchmark: bool) -> str:
    """Build a transparent note about limited single-claim context."""

    claim_row = claim_df.iloc[0]
    note = (
        "Duplicate and provider-pattern checks are limited because no historical claim list was "
        f"supplied in the request. Proxy context used previous_claim_count_90d={int(claim_row['previous_claim_count_90d'])} "
        f"and same_provider_claim_count_30d={int(claim_row['same_provider_claim_count_30d'])}."
    )
    if not used_reference_benchmark:
        note += " The abnormal billing comparison also ran without the optional synthetic benchmark portfolio."
    return note


@router.post("")
def score_claim(payload: ClaimInput) -> dict[str, object]:
    """Score a single synthetic claim payload for prototype demonstrations."""

    claim_df = pd.DataFrame([payload.model_dump()])

    try:
        abnormal_billing_flags_df, used_reference_benchmark = _flag_abnormal_billing_with_reference(claim_df)
        flags_df = _combine_flag_frames(
            [
                flag_diagnosis_treatment_mismatch(claim_df),
                flag_missing_documents(claim_df),
                abnormal_billing_flags_df,
                _flag_provider_proxy_risk(claim_df),
            ]
        )
        scored_df = calculate_risk_scores(claim_df, flags_df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    score_row = scored_df.iloc[0]
    explanation = generate_claim_explanation(str(payload.claim_id), flags_df)
    explanation = f"{explanation} {_build_limitation_note(claim_df, used_reference_benchmark)}"

    flags_output = [
        {
            "rule_name": row["rule_name"],
            "severity": row["severity"],
            "points": int(row["points"]),
            "explanation": row["explanation"],
        }
        for _, row in flags_df.iterrows()
    ]

    return jsonable_encoder(
        {
            "claim_id": payload.claim_id,
            "total_risk_score": int(score_row["total_risk_score"]),
            "risk_band": str(score_row["risk_band"]),
            "recommended_action": str(score_row["recommended_action"]),
            "flags": flags_output,
            "explanation": explanation,
            "disclaimer": DISCLAIMER_TEXT,
        }
    )
