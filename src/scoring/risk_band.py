"""Risk band and review-action helpers for ClaimGuard scoring."""

from __future__ import annotations

RISK_BAND_ORDER = [
    "Low Risk",
    "Medium Risk",
    "High Risk",
    "Critical Risk",
]

RISK_BAND_THRESHOLDS = {
    "Low Risk": (0, 24),
    "Medium Risk": (25, 49),
    "High Risk": (50, 74),
    "Critical Risk": (75, 100),
}

RECOMMENDED_ACTIONS = {
    "Low Risk": "Fast-track standard review",
    "Medium Risk": "Standard review with attention to flagged items",
    "High Risk": "Maker-checker review required",
    "Critical Risk": "Escalate for detailed investigation before approval",
}


def assign_risk_band(score: int) -> str:
    """Return the configured risk band for a capped numeric score."""

    capped_score = max(0, min(int(score), 100))
    for risk_band, (minimum_score, maximum_score) in RISK_BAND_THRESHOLDS.items():
        if minimum_score <= capped_score <= maximum_score:
            return risk_band
    return "Low Risk"


def assign_recommended_action(risk_band: str) -> str:
    """Return the default review action for a risk band."""

    return RECOMMENDED_ACTIONS.get(
        risk_band,
        "Standard review with attention to flagged items",
    )


def risk_band_sort_value(risk_band: str) -> int:
    """Return a sortable numeric order for risk bands."""

    try:
        return RISK_BAND_ORDER.index(risk_band)
    except ValueError:
        return -1
