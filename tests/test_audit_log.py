"""Tests for persisted audit-log helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.workflow.audit_log import (
    append_audit_record,
    audit_records_to_frame,
    build_seed_audit_records,
    derive_status_overrides,
    load_audit_records,
    save_audit_records,
)


def test_audit_records_can_round_trip_to_csv() -> None:
    records = build_seed_audit_records(["CLM-1", "CLM-2", "CLM-3"])
    audit_path = Path(__file__).resolve().parents[1] / "pytest-cache-files-audit-log.csv"

    assert save_audit_records(audit_path, records) is True
    loaded_records = load_audit_records(audit_path)

    assert len(loaded_records) == 3
    assert loaded_records[0]["claim_id"] == "CLM-3"


def test_append_audit_record_and_derive_latest_status() -> None:
    records = build_seed_audit_records(["CLM-1", "CLM-2", "CLM-3"])
    records = append_audit_record(
        records,
        claim_id="CLM-1",
        action="Marked as reviewed",
        reviewer_role="Claims Officer",
        previous_status="Under Review",
        new_status="Reviewed",
        note="Review completed.",
        timestamp=pd.Timestamp("2026-04-28 11:00"),
    )

    overrides = derive_status_overrides(records)

    assert overrides["CLM-1"] == "Reviewed"
    assert overrides["CLM-2"] == "Ready for Checker"


def test_audit_records_to_frame_sorts_most_recent_first() -> None:
    records = append_audit_record(
        [],
        claim_id="CLM-9",
        action="Escalated",
        reviewer_role="Senior Reviewer",
        previous_status="Ready for Checker",
        new_status="Escalated",
        note="Needs follow-up.",
        timestamp=pd.Timestamp("2026-04-28 12:00"),
    )
    records = append_audit_record(
        records,
        claim_id="CLM-8",
        action="Marked as reviewed",
        reviewer_role="Claims Officer",
        previous_status="Submitted",
        new_status="Reviewed",
        note="Reviewed.",
        timestamp=pd.Timestamp("2026-04-28 13:00"),
    )

    frame = audit_records_to_frame(records)

    assert frame.iloc[0]["claim_id"] == "CLM-8"
