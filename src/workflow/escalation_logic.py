"""Escalation helpers for the claims review workflow."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig


def requires_manual_escalation(claim_row: pd.Series | dict[str, Any]) -> bool:
    """Return whether a claim needs maker-checker escalation."""

    trigger_value = str(dict(claim_row).get("escalation_trigger", "")).strip().lower()
    return trigger_value == "yes"


def evaluate_manual_escalation(
    claim_row: pd.Series,
    rules_config: RiskRulesConfig,
) -> list[dict[str, Any]]:
    """Return workflow escalation findings for a single claim."""

    findings: list[dict[str, Any]] = []
    rule = rules_config.rules["manual_escalation"]

    if rule.enabled and requires_manual_escalation(claim_row):
        findings.append(
            {
                "rule_name": "manual_escalation",
                "weight": rule.weight,
                "reason": "Workflow escalation trigger requires maker-checker verification.",
            }
        )

    return findings


def determine_review_action(score: int, requires_escalation: bool) -> str:
    """Map a score and escalation signal to a review action."""

    if requires_escalation and score >= 60:
        return "Priority maker-checker review"
    if score >= 60:
        return "Priority review"
    if score >= 30:
        return "Queue for analyst review"
    return "Standard review"
