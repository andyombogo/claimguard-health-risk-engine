"""Claim Risk Profile page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard_utils import (
    apply_dashboard_theme,
    apply_status_overrides,
    build_claim_profile_data,
    find_related_claims,
    get_dashboard_data,
    initialize_dashboard_state,
    register_claim_action,
)

apply_dashboard_theme()
claims_df, flags_df, scored_df, queue_df = get_dashboard_data()
initialize_dashboard_state(claims_df)
queue_df = apply_status_overrides(queue_df)

st.title("Claim Risk Profile")
st.caption(
    "Inspect the claim summary, review flags, related claims, and workflow actions for a selected claim."
)

claim_options = queue_df.sort_values(
    ["total_risk_score", "claim_date"],
    ascending=[False, False],
)["claim_id"].astype(str).tolist()

default_claim_id = st.session_state.get("selected_claim_id", claim_options[0])
default_index = claim_options.index(default_claim_id) if default_claim_id in claim_options else 0
selected_claim_id = st.selectbox("Select claim ID", options=claim_options, index=default_index)
st.session_state["selected_claim_id"] = selected_claim_id

if st.session_state.get("dashboard_flash_message"):
    st.success(st.session_state.pop("dashboard_flash_message"))

profile = build_claim_profile_data(claims_df, flags_df, queue_df, selected_claim_id)
queue_row = profile.get("queue_row", {})
flag_details_df = flags_df.loc[
    flags_df["claim_id"].astype(str) == selected_claim_id
].sort_values(["points", "rule_name"], ascending=[False, True])
related_claims_df = find_related_claims(queue_df, selected_claim_id)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Risk Score", int(profile["risk_score"]))
metric_two.metric("Risk Band", str(profile["risk_band"]))
metric_three.metric("Review Flags", len(profile["flagged_rules"]))
metric_four.metric("Current Status", str(queue_row.get("claim_status", "Submitted")))

summary_left, summary_right = st.columns((1.05, 0.95))
with summary_left:
    st.subheader("Claim Summary")
    summary_fields = {
        "Claim ID": queue_row.get("claim_id"),
        "Member ID": queue_row.get("member_id"),
        "Provider": queue_row.get("provider_name"),
        "Provider Type": queue_row.get("provider_type"),
        "Claim Date": queue_row.get("claim_date"),
        "Diagnosis": queue_row.get("diagnosis_description"),
        "Procedure": queue_row.get("procedure_description"),
        "Claim Amount": queue_row.get("claim_amount"),
        "Approved Amount": queue_row.get("approved_amount"),
        "Claim Status": queue_row.get("claim_status"),
    }
    st.dataframe(
        pd.DataFrame(summary_fields.items(), columns=["Field", "Value"]),
        use_container_width=True,
        hide_index=True,
    )

with summary_right:
    st.subheader("Recommended Action")
    st.write(str(profile["recommended_action"]))
    st.subheader("Explanation")
    if profile["explanations"]:
        for explanation in profile["explanations"]:
            st.markdown(f"- {explanation}")
    else:
        st.write(
            "No review flags were triggered for this claim in the current rule set."
        )

st.subheader("Flagged Rules")
if not flag_details_df.empty:
    st.dataframe(
        flag_details_df[
            ["rule_name", "severity", "points", "explanation"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "points": st.column_config.NumberColumn("Points", format="%d"),
        },
    )
else:
    st.info("No active review flags were found for this claim.")

st.subheader("Similar Or Related Claims")
if related_claims_df.empty:
    st.write(
        "No closely related claims were found using the current same-member and same-provider diagnosis checks."
    )
else:
    st.dataframe(
        related_claims_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "claim_amount": st.column_config.NumberColumn("Claim Amount", format="%.2f"),
            "total_risk_score": st.column_config.NumberColumn("Risk Score", format="%d"),
        },
    )

note_key = f"claim_note_{selected_claim_id}"
existing_note = st.session_state.get("claim_notes", {}).get(selected_claim_id, "")
reviewer_note = st.text_area(
    "Reviewer Note",
    value=existing_note,
    key=note_key,
    height=140,
    placeholder="Capture the reviewer context, verification steps, and follow-up notes here.",
)
st.session_state.setdefault("claim_notes", {})[selected_claim_id] = reviewer_note

button_one, button_two, button_three = st.columns(3)
with button_one:
    if st.button("Mark As Reviewed", use_container_width=True):
        note = reviewer_note or "Reviewed with current claim context and risk indicators."
        register_claim_action(
            queue_df,
            claim_id=selected_claim_id,
            action="Marked as reviewed",
            reviewer_role="Claims Officer",
            new_status="Reviewed",
            note=note,
        )
        st.session_state["dashboard_flash_message"] = (
            f"Claim {selected_claim_id} marked as reviewed."
        )
        st.rerun()

with button_two:
    if st.button("Send To Checker", use_container_width=True):
        note = reviewer_note or "Escalated to checker for second-level review."
        register_claim_action(
            queue_df,
            claim_id=selected_claim_id,
            action="Sent to checker",
            reviewer_role="Claims Officer",
            new_status="Ready for Checker",
            note=note,
        )
        st.session_state["dashboard_flash_message"] = (
            f"Claim {selected_claim_id} sent to checker."
        )
        st.rerun()

with button_three:
    if st.button("Escalate", use_container_width=True):
        note = reviewer_note or "Escalated for additional verification before approval."
        register_claim_action(
            queue_df,
            claim_id=selected_claim_id,
            action="Escalated",
            reviewer_role="Senior Reviewer",
            new_status="Escalated",
            note=note,
        )
        st.session_state["dashboard_flash_message"] = (
            f"Claim {selected_claim_id} escalated for follow-up."
        )
        st.rerun()
