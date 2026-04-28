"""Rule runner for the ClaimGuard validation engine."""

from __future__ import annotations

import pandas as pd

from src.config.settings import load_risk_rules_config
from src.rules._shared import RULE_OUTPUT_COLUMNS
from src.rules.abnormal_billing import flag_abnormal_billing
from src.rules.diagnosis_treatment_check import flag_diagnosis_treatment_mismatch
from src.rules.document_completeness import flag_missing_documents
from src.rules.duplicate_claims import flag_exact_duplicates, flag_near_duplicates
from src.rules.provider_pattern_check import flag_provider_pattern_risk


def _configured_rule(rule_name: str) -> tuple[bool, dict[str, object]]:
    """Return YAML enabled state and parameters, falling back to defaults on config issues."""

    try:
        config = load_risk_rules_config()
    except Exception:
        return True, {}

    rule = config.rules.get(rule_name)
    if rule is None:
        return True, {}
    return rule.enabled, rule.parameters


def run_all_rules(df: pd.DataFrame, include_all: bool = False) -> pd.DataFrame:
    """Run all available validation rules and return a long-format flags table."""

    exact_enabled, _ = _configured_rule("exact_duplicate_claim")
    near_enabled, near_duplicate_parameters = _configured_rule("near_duplicate_claim")
    billing_enabled, abnormal_billing_parameters = _configured_rule("abnormal_billing")
    mismatch_enabled, _ = _configured_rule("diagnosis_treatment_mismatch")
    provider_enabled, provider_pattern_parameters = _configured_rule("provider_pattern_risk")
    documents_enabled, _ = _configured_rule("missing_documents")

    rule_outputs = []
    if exact_enabled:
        rule_outputs.append(flag_exact_duplicates(df))
    if near_enabled:
        rule_outputs.append(flag_near_duplicates(df, **near_duplicate_parameters))
    if billing_enabled:
        rule_outputs.append(flag_abnormal_billing(df, **abnormal_billing_parameters))
    if mismatch_enabled:
        rule_outputs.append(flag_diagnosis_treatment_mismatch(df))
    if provider_enabled:
        rule_outputs.append(flag_provider_pattern_risk(df, **provider_pattern_parameters))
    if documents_enabled:
        rule_outputs.append(flag_missing_documents(df))

    if not rule_outputs:
        return pd.DataFrame(columns=RULE_OUTPUT_COLUMNS)
    combined_df = pd.concat(rule_outputs, ignore_index=True)

    if not include_all:
        combined_df = combined_df.loc[combined_df["flag_status"]].copy()

    if combined_df.empty:
        return pd.DataFrame(columns=RULE_OUTPUT_COLUMNS)

    return combined_df.sort_values(
        by=["claim_id", "points", "rule_name"],
        ascending=[True, False, True],
    ).reset_index(drop=True)
