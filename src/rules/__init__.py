"""Rule evaluation package for explainable claim checks."""

from src.rules.abnormal_billing import flag_abnormal_billing
from src.rules.abnormal_billing import evaluate_abnormal_billing
from src.rules.diagnosis_treatment_check import flag_diagnosis_treatment_mismatch
from src.rules.diagnosis_treatment_check import evaluate_diagnosis_treatment_check
from src.rules.document_completeness import flag_missing_documents
from src.rules.document_completeness import evaluate_document_completeness
from src.rules.duplicate_claims import flag_exact_duplicates, flag_near_duplicates
from src.rules.duplicate_claims import evaluate_duplicate_claims
from src.rules.provider_pattern_check import (
    compute_provider_risk_summary,
    flag_provider_pattern_risk,
)
from src.rules.provider_pattern_check import evaluate_provider_pattern_check
from src.rules.run_all_rules import run_all_rules

__all__ = [
    "compute_provider_risk_summary",
    "flag_abnormal_billing",
    "flag_diagnosis_treatment_mismatch",
    "flag_exact_duplicates",
    "flag_missing_documents",
    "flag_near_duplicates",
    "flag_provider_pattern_risk",
    "evaluate_abnormal_billing",
    "evaluate_diagnosis_treatment_check",
    "evaluate_document_completeness",
    "evaluate_duplicate_claims",
    "evaluate_provider_pattern_check",
    "run_all_rules",
]
