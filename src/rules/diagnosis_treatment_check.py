"""Diagnosis and treatment compatibility validation rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config.settings import RiskRulesConfig
from src.rules._shared import (
    flag_rows_to_findings,
    initialize_rule_output,
    normalize_claims_dataframe,
)

RULE_NAME = "diagnosis_treatment_mismatch"
_REQUIRED_COLUMNS = ["claim_id", "diagnosis_code", "procedure_code"]


def load_allowed_diagnosis_procedure_map() -> dict[str, set[str]]:
    """Return the internal mapping of expected procedures per diagnosis code."""

    return {
        "J18": {"PRC-CHEST-XRAY", "PRC-RESP-OBS", "PRC-IV-ABX"},
        "E11": {"PRC-GLUCOSE-PANEL", "PRC-ENDO-REVIEW", "PRC-DIAB-COUNSEL", "LAB-FLU"},
        "I10": {"PRC-BP-MONITOR", "PRC-CARDIO-REVIEW", "PRC-ECG"},
        "N39": {"PRC-URINE-CULTURE", "PRC-GP-CONSULT", "PRC-RENAL-US"},
        "M54": {"PRC-PHYSIO-SESSION", "PRC-ORTHO-REVIEW", "PRC-LSPINE-XRAY"},
        "S93": {"PRC-ANKLE-XRAY", "PRC-BANDAGE-CARE", "PRC-ORTHO-REVIEW", "ORTHO-KNEE"},
        "K02": {"PRC-DENTAL-FILLING", "PRC-DENTAL-EXAM", "PRC-DENTAL-XRAY", "DENT-RESTORE"},
        "O80": {"PRC-MATERNITY-PACKAGE", "PRC-OBS-REVIEW", "PRC-POSTNATAL-OBS"},
        "A09": {"PRC-IV-FLUID", "PRC-STOOL-TEST", "PRC-GP-CONSULT"},
        "L20": {"PRC-DERM-CONSULT", "PRC-ALLERGY-PANEL"},
        "H10": {"PRC-EYE-CONSULT", "PRC-EYE-SWAB"},
        "R51": {"PRC-GP-CONSULT", "PRC-NEURO-REVIEW", "PRC-HEAD-CT"},
        "J11": {"LAB-FLU"},
        "K21": {"CONSULT-GEN"},
    }


def flag_diagnosis_treatment_mismatch(df: pd.DataFrame) -> pd.DataFrame:
    """Flag claims whose procedure is not expected for the recorded diagnosis."""

    normalized_df = normalize_claims_dataframe(df, _REQUIRED_COLUMNS, RULE_NAME)
    output_df = initialize_rule_output(normalized_df, RULE_NAME)

    allowed_map = load_allowed_diagnosis_procedure_map()
    diagnosis_codes = normalized_df["diagnosis_code"].astype(str)
    procedure_codes = normalized_df["procedure_code"].astype(str)

    flagged_mask = diagnosis_codes.map(lambda code: code in allowed_map) & ~pd.Series(
        [
            procedure_code in allowed_map.get(diagnosis_code, set())
            for diagnosis_code, procedure_code in zip(diagnosis_codes, procedure_codes)
        ],
        index=normalized_df.index,
    )

    output_df.loc[flagged_mask, "flag_status"] = True
    output_df.loc[flagged_mask, "severity"] = "medium"
    output_df.loc[flagged_mask, "points"] = 20
    output_df.loc[flagged_mask, "explanation"] = [
        (
            f"Procedure {procedure_code} is not in the expected list for diagnosis "
            f"{diagnosis_code}. Expected procedures include: "
            f"{', '.join(sorted(allowed_map.get(diagnosis_code, set())))}."
        )
        for diagnosis_code, procedure_code in zip(
            diagnosis_codes.loc[flagged_mask],
            procedure_codes.loc[flagged_mask],
        )
    ]

    return output_df


def evaluate_diagnosis_treatment_check(
    claim_row: pd.Series,
    claims_df: pd.DataFrame | RiskRulesConfig | None = None,
    rules_config: RiskRulesConfig | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns mismatch findings for one claim."""

    if isinstance(claims_df, RiskRulesConfig):
        rules_config = claims_df
        claims_df = None

    if isinstance(claims_df, pd.DataFrame):
        rule_output_df = flag_diagnosis_treatment_mismatch(claims_df)
        claim_id = str(claim_row.get("claim_id", ""))
        claim_findings_df = rule_output_df.loc[
            (rule_output_df["claim_id"] == claim_id) & (rule_output_df["flag_status"])
        ]
        return flag_rows_to_findings(claim_findings_df)

    allowed_map = load_allowed_diagnosis_procedure_map()
    diagnosis_code = str(claim_row.get("diagnosis_code", ""))
    procedure_code = str(claim_row.get("procedure_code", claim_row.get("treatment_code", "")))

    if diagnosis_code in allowed_map and procedure_code not in allowed_map[diagnosis_code]:
        return [
            {
                "rule_name": RULE_NAME,
                "weight": 20,
                "reason": (
                    f"Procedure {procedure_code} is not in the expected list for diagnosis "
                    f"{diagnosis_code}."
                ),
                "severity": "medium",
            }
        ]

    if rules_config is not None and "diagnosis_treatment_check" in rules_config.rules:
        flagged_pairs = rules_config.rules["diagnosis_treatment_check"].parameters.get(
            "flagged_pairs",
            [],
        )
        for pair in flagged_pairs:
            if diagnosis_code.startswith(pair["diagnosis_prefix"]) and procedure_code.startswith(
                pair["treatment_prefix"]
            ):
                return [
                    {
                        "rule_name": RULE_NAME,
                        "weight": 20,
                        "reason": (
                            "Diagnosis and treatment combination requires human verification "
                            "before routine progression."
                        ),
                        "severity": "medium",
                    }
                ]

    return []
