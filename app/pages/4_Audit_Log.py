"""Audit Log page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard_utils import (
    apply_dashboard_theme,
    apply_status_overrides,
    get_audit_log_df,
    get_dashboard_data,
    initialize_dashboard_state,
    plotly_white_template,
)
from src.workflow.maker_checker import assign_maker_checker

apply_dashboard_theme()
claims_df, flags_df, scored_df, queue_df = get_dashboard_data()
initialize_dashboard_state(claims_df)
queue_df = apply_status_overrides(queue_df)
audit_log_df = get_audit_log_df()

st.title("Audit Log")
st.caption(
    "Review recent workflow actions and a mock maker-checker summary for the current dashboard session."
)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Logged Actions", f"{len(audit_log_df):,}")
metric_two.metric(
    "Reviewed Claims",
    f"{int((queue_df['claim_status'] == 'Reviewed').sum()):,}",
)
metric_three.metric(
    "Ready For Checker",
    f"{int((queue_df['claim_status'] == 'Ready for Checker').sum()):,}",
)
metric_four.metric(
    "Escalated Claims",
    f"{int((queue_df['claim_status'] == 'Escalated').sum()):,}",
)

st.subheader("Recent Review Actions")
st.dataframe(
    audit_log_df[
        [
            "timestamp",
            "claim_id",
            "action",
            "reviewer_role",
            "previous_status",
            "new_status",
            "note",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

chart_left, chart_right = st.columns(2)
with chart_left:
    if not audit_log_df.empty:
        action_counts_df = (
            audit_log_df.groupby("action", as_index=False)
            .agg(action_count=("claim_id", "count"))
            .sort_values("action_count", ascending=False)
        )
        action_chart = px.bar(
            action_counts_df,
            x="action",
            y="action_count",
            template=plotly_white_template(),
            title="Recent Audit Actions",
            color="action",
        )
        action_chart.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=55, b=20),
        )
        st.plotly_chart(action_chart, use_container_width=True)

with chart_right:
    workflow_status_df = (
        queue_df.groupby("claim_status", as_index=False)
        .agg(claim_count=("claim_id", "count"))
        .sort_values("claim_count", ascending=False)
    )
    status_chart = px.bar(
        workflow_status_df,
        x="claim_status",
        y="claim_count",
        template=plotly_white_template(),
        title="Current Workflow Status Mix",
        color="claim_status",
    )
    status_chart.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=20),
    )
    st.plotly_chart(status_chart, use_container_width=True)

st.subheader("Maker-Checker Workflow Summary")
workflow_df = assign_maker_checker(scored_df).merge(
    queue_df[["claim_id", "claim_status", "provider_name"]],
    on="claim_id",
    how="left",
)
st.dataframe(
    workflow_df[
        [
            "claim_id",
            "provider_name",
            "risk_band",
            "recommended_action",
            "checker_required",
            "checker_owner",
            "claim_status",
        ]
    ].sort_values(["checker_required", "risk_band"], ascending=[False, False]),
    use_container_width=True,
    hide_index=True,
)
