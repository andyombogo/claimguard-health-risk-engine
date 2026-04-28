"""Persistent audit-log helpers for the ClaimGuard review workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

AUDIT_LOG_COLUMNS = [
    "timestamp",
    "claim_id",
    "action",
    "reviewer_role",
    "previous_status",
    "new_status",
    "note",
]


def build_seed_audit_records(claim_ids: Iterable[str]) -> list[dict[str, str]]:
    """Create a small synthetic audit history for first-run demos."""

    ids = [str(claim_id) for claim_id in claim_ids][:3]
    if not ids:
        return []

    while len(ids) < 3:
        ids.append(ids[-1])

    seed_time = pd.Timestamp("2026-04-28 09:00:00")
    return [
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": ids[0],
            "action": "Initial triage completed",
            "reviewer_role": "Claims Officer",
            "previous_status": "Submitted",
            "new_status": "Under Review",
            "note": "Claim reviewed against the current rule set and queued for attention.",
        },
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": ids[1],
            "action": "Sent to checker",
            "reviewer_role": "Claims Officer",
            "previous_status": "Under Review",
            "new_status": "Ready for Checker",
            "note": "Raised for second-level review because of multiple risk indicators.",
        },
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=47)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": ids[2],
            "action": "Escalated for follow-up",
            "reviewer_role": "Senior Reviewer",
            "previous_status": "Ready for Checker",
            "new_status": "Escalated",
            "note": "Further verification recommended before approval.",
        },
    ]


def normalize_audit_records(records: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    """Return audit records with consistent string keys and values."""

    normalized: list[dict[str, str]] = []
    for record in records:
        normalized.append(
            {
                column: "" if pd.isna(record.get(column, "")) else str(record.get(column, ""))
                for column in AUDIT_LOG_COLUMNS
            }
        )
    return normalized


def audit_records_to_frame(records: Iterable[dict[str, object]]) -> pd.DataFrame:
    """Convert audit records to a sorted dataframe."""

    audit_log_df = pd.DataFrame(normalize_audit_records(records), columns=AUDIT_LOG_COLUMNS)
    if audit_log_df.empty:
        return pd.DataFrame(columns=AUDIT_LOG_COLUMNS)

    audit_log_df["timestamp"] = pd.to_datetime(audit_log_df["timestamp"], errors="coerce")
    audit_log_df = audit_log_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    audit_log_df["timestamp"] = audit_log_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    audit_log_df["timestamp"] = audit_log_df["timestamp"].fillna("")
    return audit_log_df


def load_audit_records(path: str | Path) -> list[dict[str, str]]:
    """Load persisted audit records from CSV, returning an empty list if unavailable."""

    target_path = Path(path)
    if not target_path.exists():
        return []

    try:
        audit_log_df = pd.read_csv(target_path, dtype=str).fillna("")
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return []

    missing_columns = [column for column in AUDIT_LOG_COLUMNS if column not in audit_log_df.columns]
    if missing_columns:
        return []

    return normalize_audit_records(audit_log_df[AUDIT_LOG_COLUMNS].to_dict(orient="records"))


def save_audit_records(path: str | Path, records: Iterable[dict[str, object]]) -> bool:
    """Persist audit records to CSV and report whether the write succeeded."""

    target_path = Path(path)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        audit_records_to_frame(records).to_csv(target_path, index=False)
    except OSError:
        return False
    return True


def append_audit_record(
    records: list[dict[str, str]],
    claim_id: str,
    action: str,
    reviewer_role: str,
    previous_status: str,
    new_status: str,
    note: str,
    timestamp: pd.Timestamp | None = None,
) -> list[dict[str, str]]:
    """Return a copy of records with one new audit event appended."""

    event_time = timestamp or pd.Timestamp.now()
    updated_records = list(records)
    updated_records.append(
        {
            "timestamp": event_time.strftime("%Y-%m-%d %H:%M"),
            "claim_id": str(claim_id),
            "action": action,
            "reviewer_role": reviewer_role,
            "previous_status": previous_status,
            "new_status": new_status,
            "note": note,
        }
    )
    return updated_records


def derive_status_overrides(records: Iterable[dict[str, object]]) -> dict[str, str]:
    """Derive the latest known workflow status per claim from audit events."""

    audit_log_df = audit_records_to_frame(records)
    if audit_log_df.empty:
        return {}

    # Sort oldest to newest so later events replace earlier statuses.
    chronological_df = audit_log_df.copy()
    chronological_df["timestamp"] = pd.to_datetime(chronological_df["timestamp"], errors="coerce")
    chronological_df = chronological_df.sort_values("timestamp", ascending=True)

    overrides: dict[str, str] = {}
    for _, row in chronological_df.iterrows():
        claim_id = str(row.get("claim_id", "")).strip()
        new_status = str(row.get("new_status", "")).strip()
        if claim_id and new_status:
            overrides[claim_id] = new_status
    return overrides
