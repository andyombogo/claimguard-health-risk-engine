"""Generate a realistic synthetic health claims dataset for the ClaimGuard demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260428
BASELINE_CLAIMS = 520
DUPLICATE_CLAIMS = 40
EXACT_OVERLAP_DUPLICATES = 12
ABNORMAL_BILLING_CLAIMS = 34
MISMATCH_CLAIMS = 28
MISSING_DOCUMENT_CLAIMS = 72
TOTAL_PROVIDERS = 65
TOTAL_MEMBERS = 260

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "synthetic" / "synthetic_health_claims.csv"


@dataclass(frozen=True)
class ProcedureOption:
    """A procedure that can legitimately occur for a diagnosis."""

    code: str
    description: str
    typical_amount: int


@dataclass(frozen=True)
class DiagnosisTemplate:
    """Synthetic diagnosis template used to produce realistic claims patterns."""

    diagnosis_code: str
    diagnosis_description: str
    accepted_procedures: tuple[ProcedureOption, ...]
    drug_codes: tuple[str, ...]
    provider_types: tuple[str, ...]
    inpatient_probability: float
    lab_report_probability: float


def make_rng() -> np.random.Generator:
    """Return a seeded random generator for reproducible datasets."""

    return np.random.default_rng(SEED)


def build_diagnosis_catalog() -> list[DiagnosisTemplate]:
    """Create a compact clinical catalogue with acceptable diagnosis-procedure pairs."""

    return [
        DiagnosisTemplate(
            diagnosis_code="J18",
            diagnosis_description="Pneumonia",
            accepted_procedures=(
                ProcedureOption("PRC-CHEST-XRAY", "Chest X-ray", 18000),
                ProcedureOption("PRC-RESP-OBS", "Respiratory observation", 42000),
                ProcedureOption("PRC-IV-ABX", "Intravenous antibiotic therapy", 56000),
            ),
            drug_codes=("DRG-AMOX-500", "DRG-AZI-250", ""),
            provider_types=("Hospital", "Clinic", "Diagnostic Center"),
            inpatient_probability=0.35,
            lab_report_probability=0.65,
        ),
        DiagnosisTemplate(
            diagnosis_code="E11",
            diagnosis_description="Type 2 diabetes mellitus",
            accepted_procedures=(
                ProcedureOption("PRC-GLUCOSE-PANEL", "Glucose panel", 8500),
                ProcedureOption("PRC-ENDO-REVIEW", "Endocrine review", 12000),
                ProcedureOption("PRC-DIAB-COUNSEL", "Diabetes counselling", 9000),
            ),
            drug_codes=("DRG-MET-500", "DRG-GLIM-2", ""),
            provider_types=("Clinic", "Hospital", "Pharmacy"),
            inpatient_probability=0.08,
            lab_report_probability=0.45,
        ),
        DiagnosisTemplate(
            diagnosis_code="I10",
            diagnosis_description="Essential hypertension",
            accepted_procedures=(
                ProcedureOption("PRC-BP-MONITOR", "Blood pressure monitoring", 6500),
                ProcedureOption("PRC-CARDIO-REVIEW", "Cardiology review", 15000),
                ProcedureOption("PRC-ECG", "Electrocardiogram", 11000),
            ),
            drug_codes=("DRG-AMLO-5", "DRG-LOS-50", ""),
            provider_types=("Clinic", "Hospital"),
            inpatient_probability=0.05,
            lab_report_probability=0.15,
        ),
        DiagnosisTemplate(
            diagnosis_code="N39",
            diagnosis_description="Urinary tract infection",
            accepted_procedures=(
                ProcedureOption("PRC-URINE-CULTURE", "Urine culture", 9500),
                ProcedureOption("PRC-GP-CONSULT", "General physician consult", 7000),
                ProcedureOption("PRC-RENAL-US", "Renal ultrasound", 22000),
            ),
            drug_codes=("DRG-NIT-100", "DRG-CIP-500", ""),
            provider_types=("Clinic", "Hospital", "Diagnostic Center"),
            inpatient_probability=0.10,
            lab_report_probability=0.55,
        ),
        DiagnosisTemplate(
            diagnosis_code="M54",
            diagnosis_description="Low back pain",
            accepted_procedures=(
                ProcedureOption("PRC-PHYSIO-SESSION", "Physiotherapy session", 10000),
                ProcedureOption("PRC-ORTHO-REVIEW", "Orthopaedic review", 14000),
                ProcedureOption("PRC-LSPINE-XRAY", "Lumbar spine X-ray", 20000),
            ),
            drug_codes=("DRG-DICLO-50", "DRG-IBU-400", ""),
            provider_types=("Clinic", "Hospital", "Diagnostic Center"),
            inpatient_probability=0.04,
            lab_report_probability=0.10,
        ),
        DiagnosisTemplate(
            diagnosis_code="S93",
            diagnosis_description="Ankle sprain",
            accepted_procedures=(
                ProcedureOption("PRC-ANKLE-XRAY", "Ankle X-ray", 17500),
                ProcedureOption("PRC-BANDAGE-CARE", "Bandage care", 9000),
                ProcedureOption("PRC-ORTHO-REVIEW", "Orthopaedic review", 15000),
            ),
            drug_codes=("DRG-IBU-400", "DRG-PARA-500", ""),
            provider_types=("Clinic", "Hospital", "Diagnostic Center"),
            inpatient_probability=0.03,
            lab_report_probability=0.12,
        ),
        DiagnosisTemplate(
            diagnosis_code="K02",
            diagnosis_description="Dental caries",
            accepted_procedures=(
                ProcedureOption("PRC-DENTAL-FILLING", "Dental filling", 16000),
                ProcedureOption("PRC-DENTAL-EXAM", "Dental examination", 6000),
                ProcedureOption("PRC-DENTAL-XRAY", "Dental X-ray", 9500),
            ),
            drug_codes=("DRG-AMOX-500", "", ""),
            provider_types=("Dental Clinic",),
            inpatient_probability=0.00,
            lab_report_probability=0.05,
        ),
        DiagnosisTemplate(
            diagnosis_code="O80",
            diagnosis_description="Normal delivery",
            accepted_procedures=(
                ProcedureOption("PRC-MATERNITY-PACKAGE", "Maternity care package", 78000),
                ProcedureOption("PRC-OBS-REVIEW", "Obstetric review", 24000),
                ProcedureOption("PRC-POSTNATAL-OBS", "Postnatal observation", 32000),
            ),
            drug_codes=("DRG-FE-PLUS", "", ""),
            provider_types=("Hospital",),
            inpatient_probability=0.92,
            lab_report_probability=0.40,
        ),
        DiagnosisTemplate(
            diagnosis_code="A09",
            diagnosis_description="Gastroenteritis",
            accepted_procedures=(
                ProcedureOption("PRC-IV-FLUID", "Intravenous fluid therapy", 15000),
                ProcedureOption("PRC-STOOL-TEST", "Stool test", 11000),
                ProcedureOption("PRC-GP-CONSULT", "General physician consult", 7000),
            ),
            drug_codes=("DRG-ORS-SET", "DRG-METRO-400", ""),
            provider_types=("Clinic", "Hospital"),
            inpatient_probability=0.10,
            lab_report_probability=0.38,
        ),
        DiagnosisTemplate(
            diagnosis_code="L20",
            diagnosis_description="Dermatitis",
            accepted_procedures=(
                ProcedureOption("PRC-DERM-CONSULT", "Dermatology consultation", 12000),
                ProcedureOption("PRC-ALLERGY-PANEL", "Allergy panel", 26000),
            ),
            drug_codes=("DRG-HC-CRM", "DRG-CET-10", ""),
            provider_types=("Clinic", "Hospital"),
            inpatient_probability=0.02,
            lab_report_probability=0.20,
        ),
        DiagnosisTemplate(
            diagnosis_code="H10",
            diagnosis_description="Conjunctivitis",
            accepted_procedures=(
                ProcedureOption("PRC-EYE-CONSULT", "Eye consultation", 9000),
                ProcedureOption("PRC-EYE-SWAB", "Eye swab test", 13500),
            ),
            drug_codes=("DRG-CHL-EYE", "DRG-ART-TEARS", ""),
            provider_types=("Clinic", "Hospital"),
            inpatient_probability=0.01,
            lab_report_probability=0.12,
        ),
        DiagnosisTemplate(
            diagnosis_code="R51",
            diagnosis_description="Headache",
            accepted_procedures=(
                ProcedureOption("PRC-GP-CONSULT", "General physician consult", 7000),
                ProcedureOption("PRC-NEURO-REVIEW", "Neurology review", 22000),
                ProcedureOption("PRC-HEAD-CT", "Head CT scan", 48000),
            ),
            drug_codes=("DRG-PARA-500", "DRG-IBU-400", ""),
            provider_types=("Clinic", "Hospital", "Diagnostic Center"),
            inpatient_probability=0.06,
            lab_report_probability=0.08,
        ),
    ]


def build_provider_catalog(rng: np.random.Generator) -> tuple[pd.DataFrame, set[str]]:
    """Create a synthetic provider directory and identify high-risk providers."""

    provider_type_choices = [
        "Hospital",
        "Clinic",
        "Pharmacy",
        "Diagnostic Center",
        "Dental Clinic",
    ]
    provider_type_weights = np.array([0.28, 0.34, 0.12, 0.14, 0.12])
    prefixes = [
        "Northfield",
        "Greenvale",
        "Silveroak",
        "Suncrest",
        "Bluebrook",
        "Lakeside",
        "Riverstone",
        "Highplain",
        "Mapleridge",
        "Oakwell",
        "Brightwater",
        "Hillcrest",
    ]
    middle_names = [
        "Family",
        "Wellness",
        "Unity",
        "Prime",
        "Community",
        "Civic",
        "Metro",
        "Care",
        "Health",
        "Medical",
        "Access",
        "Vital",
    ]
    suffix_lookup = {
        "Hospital": "General Hospital",
        "Clinic": "Care Clinic",
        "Pharmacy": "Pharmacy Hub",
        "Diagnostic Center": "Diagnostic Hub",
        "Dental Clinic": "Dental Studio",
    }

    provider_types = rng.choice(
        provider_type_choices,
        size=TOTAL_PROVIDERS,
        p=provider_type_weights,
    )
    records: list[dict[str, str]] = []
    for index, provider_type in enumerate(provider_types, start=1):
        provider_id = f"PRV-{index:04d}"
        prefix = rng.choice(prefixes)
        middle_name = rng.choice(middle_names)
        provider_name = f"{prefix} {middle_name} {suffix_lookup[provider_type]} {index:02d}"
        records.append(
            {
                "provider_id": provider_id,
                "provider_name": provider_name,
                "provider_type": provider_type,
            }
        )

    provider_df = pd.DataFrame(records)

    high_risk_provider_ids: list[str] = []
    for provider_type in ["Hospital", "Clinic", "Diagnostic Center", "Pharmacy", "Hospital", "Clinic"]:
        available = provider_df.loc[
            (provider_df["provider_type"] == provider_type)
            & (~provider_df["provider_id"].isin(high_risk_provider_ids))
        ]
        if not available.empty:
            high_risk_provider_ids.append(str(available.iloc[0]["provider_id"]))

    return provider_df, set(high_risk_provider_ids)


def build_member_catalog() -> tuple[pd.DataFrame, set[str]]:
    """Create a pool of fake members and a smaller high-frequency segment."""

    records = [{"member_id": f"MBR-{index:06d}"} for index in range(1, TOTAL_MEMBERS + 1)]
    member_df = pd.DataFrame(records)
    high_frequency_members = set(member_df.head(14)["member_id"].tolist())
    return member_df, high_frequency_members


def choose_provider(
    template: DiagnosisTemplate,
    providers_df: pd.DataFrame,
    high_risk_provider_ids: set[str],
    rng: np.random.Generator,
) -> pd.Series:
    """Select a provider, with a bias toward riskier providers for some claims."""

    candidates = providers_df.loc[providers_df["provider_type"].isin(template.provider_types)]
    risky_candidates = candidates.loc[candidates["provider_id"].isin(high_risk_provider_ids)]

    if not risky_candidates.empty and rng.random() < 0.34:
        return risky_candidates.sample(n=1, random_state=int(rng.integers(1, 1_000_000))).iloc[0]

    return candidates.sample(n=1, random_state=int(rng.integers(1, 1_000_000))).iloc[0]


def choose_member(
    members_df: pd.DataFrame,
    high_frequency_member_ids: set[str],
    rng: np.random.Generator,
) -> str:
    """Select a member, with a bias toward members used in frequency-pattern demos."""

    if rng.random() < 0.22:
        return str(rng.choice(sorted(high_frequency_member_ids)))
    return str(rng.choice(members_df["member_id"].to_numpy()))


def round_amount(value: float) -> float:
    """Round synthetic claim values to realistic billing increments."""

    return float(int(round(value / 50.0) * 50))


def sample_claim_dates(
    template: DiagnosisTemplate,
    rng: np.random.Generator,
) -> tuple[pd.Timestamp, pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]:
    """Generate logically ordered claim, admission, and discharge dates."""

    service_start = pd.Timestamp("2026-01-01") + pd.Timedelta(days=int(rng.integers(0, 181)))

    if rng.random() < template.inpatient_probability:
        admission_date = service_start
        length_of_stay = int(rng.integers(1, 6))
        discharge_date = admission_date + pd.Timedelta(days=length_of_stay)
        claim_date = discharge_date + pd.Timedelta(days=int(rng.integers(1, 8)))
        return claim_date, admission_date, discharge_date

    claim_date = service_start + pd.Timedelta(days=int(rng.integers(0, 5)))
    return claim_date, pd.NaT, pd.NaT


def default_document_flags(
    template: DiagnosisTemplate,
    admission_date: pd.Timestamp | pd.NaT,
    rng: np.random.Generator,
) -> tuple[bool, bool, bool]:
    """Generate baseline document availability before injecting risky gaps."""

    # Most claims start with a clean document profile so the injected missing-document
    # scenarios remain visible and useful in demos. For non-inpatient claims,
    # `has_discharge_summary=True` represents a satisfied document check rather than a
    # literal discharge note attachment.
    has_invoice = bool(rng.random() < 0.98)
    has_discharge_summary = bool(rng.random() < (0.96 if pd.notna(admission_date) else 0.94))
    has_lab_report = bool(rng.random() < max(0.88, template.lab_report_probability))
    return has_invoice, has_discharge_summary, has_lab_report


def sample_claim_amount(
    procedure: ProcedureOption,
    is_high_risk_provider: bool,
    rng: np.random.Generator,
) -> float:
    """Generate realistic baseline claim amounts."""

    multiplier = np.clip(rng.normal(loc=1.0, scale=0.18), 0.65, 1.55)
    if is_high_risk_provider:
        multiplier *= float(rng.uniform(1.12, 1.35))
    return round_amount(procedure.typical_amount * multiplier)


def build_base_claim_record(
    claim_number: int,
    template: DiagnosisTemplate,
    provider_row: pd.Series,
    member_id: str,
    rng: np.random.Generator,
    high_risk_provider_ids: set[str],
) -> dict[str, object]:
    """Construct a single baseline synthetic claim row."""

    procedure = rng.choice(template.accepted_procedures)
    claim_date, admission_date, discharge_date = sample_claim_dates(template, rng)
    has_invoice, has_discharge_summary, has_lab_report = default_document_flags(
        template,
        admission_date,
        rng,
    )
    drug_code = str(rng.choice(template.drug_codes))
    is_high_risk_provider = str(provider_row["provider_id"]) in high_risk_provider_ids

    return {
        "claim_id": f"CLM-{claim_number:06d}",
        "member_id": member_id,
        "provider_id": str(provider_row["provider_id"]),
        "provider_name": str(provider_row["provider_name"]),
        "provider_type": str(provider_row["provider_type"]),
        "claim_date": claim_date.normalize(),
        "admission_date": admission_date.normalize() if pd.notna(admission_date) else pd.NaT,
        "discharge_date": discharge_date.normalize() if pd.notna(discharge_date) else pd.NaT,
        "diagnosis_code": template.diagnosis_code,
        "diagnosis_description": template.diagnosis_description,
        "procedure_code": procedure.code,
        "procedure_description": procedure.description,
        "drug_code": "" if drug_code == "" else drug_code,
        "claim_amount": sample_claim_amount(procedure, is_high_risk_provider, rng),
        "approved_amount": 0.0,
        "document_count": 0,
        "has_invoice": has_invoice,
        "has_discharge_summary": has_discharge_summary,
        "has_lab_report": has_lab_report,
        "previous_claim_count_90d": 0,
        "same_provider_claim_count_30d": 0,
        "claim_channel": str(
            rng.choice(
                [
                    "Provider Portal",
                    "Member App",
                    "Email Submission",
                    "Branch Desk",
                    "Batch Upload",
                ],
                p=[0.38, 0.18, 0.12, 0.14, 0.18],
            )
        ),
        "claim_status": "Submitted",
        "reviewer_decision": "Pending Review",
        "known_review_outcome": "Awaiting initial review",
        "_duplicate_pattern": False,
        "_abnormal_billing_pattern": False,
        "_mismatch_pattern": False,
        "_missing_documents_pattern": False,
        "_high_risk_provider": is_high_risk_provider,
    }


def generate_base_claims(
    providers_df: pd.DataFrame,
    members_df: pd.DataFrame,
    templates: list[DiagnosisTemplate],
    high_risk_provider_ids: set[str],
    high_frequency_member_ids: set[str],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate the baseline portion of the synthetic dataset."""

    template_weights = np.array([0.12, 0.11, 0.10, 0.10, 0.08, 0.08, 0.07, 0.06, 0.09, 0.06, 0.05, 0.08])
    template_weights = template_weights / template_weights.sum()

    records: list[dict[str, object]] = []
    for claim_number in range(1, BASELINE_CLAIMS + 1):
        template = rng.choice(templates, p=template_weights)
        provider_row = choose_provider(template, providers_df, high_risk_provider_ids, rng)
        member_id = choose_member(members_df, high_frequency_member_ids, rng)
        records.append(
            build_base_claim_record(
                claim_number=claim_number,
                template=template,
                provider_row=provider_row,
                member_id=member_id,
                rng=rng,
                high_risk_provider_ids=high_risk_provider_ids,
            )
        )

    return pd.DataFrame(records)


def clone_duplicate_claims(
    claims_df: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Append duplicate and near-duplicate claims to support duplicate-detection demos."""

    candidate_pool = claims_df.loc[
        claims_df["_high_risk_provider"] | claims_df["member_id"].isin(claims_df["member_id"].value_counts().head(20).index)
    ]
    source_indices = rng.choice(candidate_pool.index.to_numpy(), size=count, replace=False)
    next_claim_number = int(claims_df["claim_id"].str.replace("CLM-", "", regex=False).astype(int).max()) + 1

    duplicates: list[dict[str, object]] = []
    for offset, source_index in enumerate(source_indices):
        source_row = claims_df.loc[source_index].copy()
        amount_shift = float(rng.uniform(0.97, 1.08))
        claim_date_shift = int(rng.integers(0, 4))

        source_row["claim_id"] = f"CLM-{next_claim_number + offset:06d}"
        source_row["claim_date"] = pd.Timestamp(source_row["claim_date"]) + pd.Timedelta(days=claim_date_shift)
        source_row["claim_amount"] = round_amount(float(source_row["claim_amount"]) * amount_shift)
        source_row["_duplicate_pattern"] = True
        source_row["claim_channel"] = str(
            rng.choice(["Provider Portal", "Batch Upload", "Email Submission"], p=[0.5, 0.35, 0.15])
        )
        duplicates.append(source_row.to_dict())

    duplicate_df = pd.DataFrame(duplicates)
    return pd.concat([claims_df, duplicate_df], ignore_index=True)


def append_exact_duplicate_overlaps(
    claims_df: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Clone already-flag-prone claims exactly to create higher-priority review examples.

    These rows are appended after the baseline pattern injections so the exact duplicate
    rule can overlap with other explainable signals such as abnormal billing,
    diagnosis-treatment mismatch, or missing documents.
    """

    working_df = claims_df.copy()
    candidate_mask = (
        working_df["_abnormal_billing_pattern"]
        | working_df["_mismatch_pattern"]
        | working_df["_missing_documents_pattern"]
    )
    candidate_indices = working_df.loc[candidate_mask].index.to_numpy()
    if len(candidate_indices) == 0:
        return working_df

    sample_size = min(count, len(candidate_indices))
    selected_indices = rng.choice(candidate_indices, size=sample_size, replace=False)
    next_claim_number = (
        int(working_df["claim_id"].str.replace("CLM-", "", regex=False).astype(int).max()) + 1
    )

    exact_duplicates: list[dict[str, object]] = []
    for offset, selected_index in enumerate(selected_indices):
        source_row = working_df.loc[selected_index].copy()
        source_row["claim_id"] = f"CLM-{next_claim_number + offset:06d}"
        source_row["claim_channel"] = str(
            rng.choice(
                ["Provider Portal", "Batch Upload", "Email Submission"],
                p=[0.45, 0.40, 0.15],
            )
        )
        source_row["_duplicate_pattern"] = True
        exact_duplicates.append(source_row.to_dict())

    return pd.concat([working_df, pd.DataFrame(exact_duplicates)], ignore_index=True)


def inject_abnormal_billing(
    claims_df: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Raise some claims to 2x-5x the median for the same diagnosis/procedure."""

    working_df = claims_df.copy()
    median_lookup = working_df.groupby(["diagnosis_code", "procedure_code"])["claim_amount"].median()
    candidate_mask = ~working_df["_duplicate_pattern"]
    candidates = working_df.loc[candidate_mask].index.to_numpy()
    selected_indices = rng.choice(candidates, size=count, replace=False)

    for selected_index in selected_indices:
        diagnosis_code = working_df.at[selected_index, "diagnosis_code"]
        procedure_code = working_df.at[selected_index, "procedure_code"]
        median_amount = float(median_lookup.loc[(diagnosis_code, procedure_code)])
        abnormal_amount = round_amount(median_amount * float(rng.uniform(2.0, 5.0)))
        working_df.at[selected_index, "claim_amount"] = max(
            abnormal_amount,
            float(working_df.at[selected_index, "claim_amount"]),
        )
        working_df.at[selected_index, "_abnormal_billing_pattern"] = True

    return working_df


def inject_diagnosis_treatment_mismatches(
    claims_df: pd.DataFrame,
    templates: list[DiagnosisTemplate],
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Swap a subset of procedures to intentionally mismatched combinations."""

    working_df = claims_df.copy()
    all_procedures = {
        procedure.code: procedure.description
        for template in templates
        for procedure in template.accepted_procedures
    }
    acceptable_lookup = {
        template.diagnosis_code: {procedure.code for procedure in template.accepted_procedures}
        for template in templates
    }

    candidate_mask = ~working_df["_duplicate_pattern"] & ~working_df["_abnormal_billing_pattern"]
    selected_indices = rng.choice(working_df.loc[candidate_mask].index.to_numpy(), size=count, replace=False)

    for selected_index in selected_indices:
        diagnosis_code = str(working_df.at[selected_index, "diagnosis_code"])
        acceptable_procedures = acceptable_lookup[diagnosis_code]
        mismatch_candidates = [code for code in all_procedures if code not in acceptable_procedures]
        mismatch_code = str(rng.choice(mismatch_candidates))
        working_df.at[selected_index, "procedure_code"] = mismatch_code
        working_df.at[selected_index, "procedure_description"] = all_procedures[mismatch_code]
        working_df.at[selected_index, "_mismatch_pattern"] = True

    return working_df


def inject_missing_documents(
    claims_df: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create targeted document gaps for completeness-check demos."""

    working_df = claims_df.copy()
    selected_indices = rng.choice(working_df.index.to_numpy(), size=count, replace=False)

    for selected_index in selected_indices:
        working_df.at[selected_index, "_missing_documents_pattern"] = True
        provider_type = str(working_df.at[selected_index, "provider_type"])

        working_df.at[selected_index, "has_invoice"] = False

        if pd.notna(working_df.at[selected_index, "admission_date"]) or provider_type == "Hospital":
            working_df.at[selected_index, "has_discharge_summary"] = False

        if provider_type in {"Diagnostic Center", "Hospital", "Clinic"}:
            if rng.random() < 0.7:
                working_df.at[selected_index, "has_lab_report"] = False

    return working_df


def compute_rolling_count(
    claims_df: pd.DataFrame,
    group_column: str,
    date_column: str,
    window_days: int,
) -> pd.Series:
    """Count prior claims inside a rolling lookback window."""

    sorted_df = claims_df.sort_values(date_column).reset_index()
    output = pd.Series(data=np.zeros(len(sorted_df), dtype=int), index=sorted_df.index)

    for _, group_data in sorted_df.groupby(group_column, sort=False):
        dates = pd.to_datetime(group_data[date_column]).to_numpy(dtype="datetime64[D]")
        positions = group_data.index.to_numpy()
        left = 0
        group_counts = np.zeros(len(positions), dtype=int)

        for right in range(len(positions)):
            current_date = dates[right]
            while current_date - dates[left] > np.timedelta64(window_days, "D"):
                left += 1
            group_counts[right] = right - left

        output.loc[positions] = group_counts

    sorted_df["computed_count"] = output
    restored = sorted_df.sort_values("index")
    return restored["computed_count"].reset_index(drop=True)


def assign_review_fields(claims_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Populate workflow fields and approved amounts after risk patterns are injected."""

    working_df = claims_df.copy()
    statuses: list[str] = []
    decisions: list[str] = []
    outcomes: list[str] = []
    approved_amounts: list[float] = []

    for _, row in working_df.iterrows():
        if bool(row["_missing_documents_pattern"]):
            status = "Pending Documents"
            decision = "Returned for Documents"
            outcome = "Pending additional documents"
            approved_amount = 0.0
        elif bool(row["_duplicate_pattern"]):
            status = "Under Review"
            decision = "Query Raised"
            outcome = "Combined with earlier submission"
            approved_amount = 0.0
        elif bool(row["_abnormal_billing_pattern"]):
            status = "Under Review"
            decision = "Escalated"
            outcome = "Escalated for tariff review"
            approved_amount = 0.0
        elif bool(row["_mismatch_pattern"]):
            status = "Under Review"
            decision = "Escalated"
            outcome = "Escalated for clinical validation"
            approved_amount = 0.0
        else:
            if rng.random() < 0.58:
                status = "Approved"
                decision = "Approved"
                outcome = "Cleared after review"
                approved_amount = round_amount(float(row["claim_amount"]) * float(rng.uniform(0.82, 1.00)))
            elif rng.random() < 0.65:
                status = "Closed"
                decision = "Approved"
                outcome = "Approved after review"
                approved_amount = round_amount(float(row["claim_amount"]) * float(rng.uniform(0.75, 0.96)))
            else:
                status = "Submitted"
                decision = "Pending Review"
                outcome = "Awaiting initial review"
                approved_amount = 0.0

        statuses.append(status)
        decisions.append(decision)
        outcomes.append(outcome)
        approved_amounts.append(min(float(row["claim_amount"]), approved_amount))

    working_df["claim_status"] = statuses
    working_df["reviewer_decision"] = decisions
    working_df["known_review_outcome"] = outcomes
    working_df["approved_amount"] = approved_amounts
    working_df["document_count"] = (
        working_df[["has_invoice", "has_discharge_summary", "has_lab_report"]]
        .astype(bool)
        .sum(axis=1)
        .astype(int)
    )

    return working_df


def finalize_claims_dataframe(claims_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Compute rolling history features and clean the final export dataset."""

    working_df = claims_df.copy()
    working_df["claim_date"] = pd.to_datetime(working_df["claim_date"])
    working_df["admission_date"] = pd.to_datetime(working_df["admission_date"])
    working_df["discharge_date"] = pd.to_datetime(working_df["discharge_date"])

    working_df = working_df.sort_values("claim_date").reset_index(drop=True)
    working_df["previous_claim_count_90d"] = compute_rolling_count(
        working_df,
        group_column="member_id",
        date_column="claim_date",
        window_days=90,
    )
    working_df["same_provider_claim_count_30d"] = compute_rolling_count(
        working_df,
        group_column="provider_id",
        date_column="claim_date",
        window_days=30,
    )

    working_df = assign_review_fields(working_df, rng)

    export_columns = [
        "claim_id",
        "member_id",
        "provider_id",
        "provider_name",
        "provider_type",
        "claim_date",
        "admission_date",
        "discharge_date",
        "diagnosis_code",
        "diagnosis_description",
        "procedure_code",
        "procedure_description",
        "drug_code",
        "claim_amount",
        "approved_amount",
        "document_count",
        "has_invoice",
        "has_discharge_summary",
        "has_lab_report",
        "previous_claim_count_90d",
        "same_provider_claim_count_30d",
        "claim_channel",
        "claim_status",
        "reviewer_decision",
        "known_review_outcome",
    ]

    export_df = working_df[export_columns].copy()
    for column_name in ["claim_date", "admission_date", "discharge_date"]:
        export_df[column_name] = pd.to_datetime(export_df[column_name]).dt.strftime("%Y-%m-%d")
        export_df[column_name] = export_df[column_name].replace("NaT", "")

    export_df["claim_amount"] = export_df["claim_amount"].round(2)
    export_df["approved_amount"] = export_df["approved_amount"].round(2)

    return export_df


def generate_synthetic_claims() -> pd.DataFrame:
    """Generate the full synthetic claims dataset."""

    rng = make_rng()
    templates = build_diagnosis_catalog()
    providers_df, high_risk_provider_ids = build_provider_catalog(rng)
    members_df, high_frequency_member_ids = build_member_catalog()

    claims_df = generate_base_claims(
        providers_df=providers_df,
        members_df=members_df,
        templates=templates,
        high_risk_provider_ids=high_risk_provider_ids,
        high_frequency_member_ids=high_frequency_member_ids,
        rng=rng,
    )
    claims_df = clone_duplicate_claims(claims_df, DUPLICATE_CLAIMS, rng)
    claims_df = inject_abnormal_billing(claims_df, ABNORMAL_BILLING_CLAIMS, rng)
    claims_df = inject_diagnosis_treatment_mismatches(claims_df, templates, MISMATCH_CLAIMS, rng)
    claims_df = inject_missing_documents(claims_df, MISSING_DOCUMENT_CLAIMS, rng)
    claims_df = append_exact_duplicate_overlaps(claims_df, EXACT_OVERLAP_DUPLICATES, rng)

    return finalize_claims_dataframe(claims_df, rng)


def save_synthetic_claims(output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    """Generate and persist the synthetic claims dataset to disk."""

    synthetic_claims_df = generate_synthetic_claims()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    synthetic_claims_df.to_csv(output_path, index=False)
    return synthetic_claims_df


def print_generation_summary(claims_df: pd.DataFrame) -> None:
    """Print a compact summary after generation."""

    duplicate_mask = claims_df.duplicated(
        subset=["member_id", "provider_id", "diagnosis_code", "procedure_code"],
        keep=False,
    )
    abnormal_threshold = claims_df.groupby(["diagnosis_code", "procedure_code"])["claim_amount"].transform("median") * 2
    abnormal_mask = claims_df["claim_amount"] >= abnormal_threshold
    catalog = build_diagnosis_catalog()
    acceptable_lookup = {
        template.diagnosis_code: {procedure.code for procedure in template.accepted_procedures}
        for template in catalog
    }
    mismatch_mask = ~claims_df.apply(
        lambda row: row["procedure_code"] in acceptable_lookup[row["diagnosis_code"]],
        axis=1,
    )
    missing_docs_mask = (~claims_df["has_invoice"]) | (~claims_df["has_discharge_summary"]) | (~claims_df["has_lab_report"])

    print(f"Saved {len(claims_df)} synthetic claims to {OUTPUT_PATH}")
    print(f"Providers: {claims_df['provider_id'].nunique()} | Members: {claims_df['member_id'].nunique()}")
    print(f"Potential duplicate clusters: {int(duplicate_mask.sum())}")
    print(f"Abnormal billing candidates: {int(abnormal_mask.sum())}")
    print(f"Diagnosis-treatment mismatch examples: {int(mismatch_mask.sum())}")
    print(f"Claims with document gaps: {int(missing_docs_mask.sum())}")


if __name__ == "__main__":
    generated_df = save_synthetic_claims()
    print_generation_summary(generated_df)
