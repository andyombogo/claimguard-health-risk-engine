"""Unit tests for workflow and review-routing helpers."""

from __future__ import annotations

import pandas as pd

from src.scoring.risk_band import assign_recommended_action
from src.workflow.maker_checker import assign_maker_checker
from src.workflow.triage_queue import build_triage_queue


def test_triage_queue_prioritizes_escalated_high_score_claims() -> None:
    claims_df = pd.DataFrame(
        {
            "claim_id": ["CLM-1", "CLM-2", "CLM-3"],
            "claim_amount": [1000, 3000, 2000],
        }
    )
    scored_df = pd.DataFrame(
        {
            "claim_id": ["CLM-1", "CLM-2", "CLM-3"],
            "risk_score": [20, 80, 60],
            "risk_band": ["Low Risk", "Critical Risk", "High Risk"],
            "requires_escalation": [False, True, True],
        }
    )

    queue_df = build_triage_queue(claims_df, scored_df)

    assert queue_df.iloc[0]["claim_id"] == "CLM-2"
    assert queue_df.iloc[1]["claim_id"] == "CLM-3"


def test_maker_checker_requires_checker_for_high_and_critical_claims() -> None:
    scored_df = pd.DataFrame(
        {
            "claim_id": ["CLM-1", "CLM-2", "CLM-3"],
            "risk_band": ["Low Risk", "High Risk", "Critical Risk"],
        }
    )

    workflow_df = assign_maker_checker(scored_df).set_index("claim_id")

    assert bool(workflow_df.loc["CLM-1", "checker_required"]) is False
    assert bool(workflow_df.loc["CLM-2", "checker_required"]) is True
    assert bool(workflow_df.loc["CLM-3", "checker_required"]) is True
    assert workflow_df.loc["CLM-3", "checker_status"] == "Pending"


def test_recommended_actions_match_review_workflow_intent() -> None:
    assert assign_recommended_action("Low Risk") == "Fast-track standard review"
    assert assign_recommended_action("High Risk") == "Maker-checker review required"
    assert assign_recommended_action("Critical Risk") == (
        "Escalate for detailed investigation before approval"
    )
