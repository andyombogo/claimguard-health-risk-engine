"""Claims Review Queue page."""

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
    get_dashboard_data,
    initialize_dashboard_state,
    sort_risk_band_frame,
    styled_bar_chart,
)

apply_dashboard_theme()
claims_df, flags_df, scored_df, queue_df = get_dashboard_data()
initialize_dashboard_state(claims_df)
queue_df = apply_status_overrides(queue_df)

st.title("Claims Review Queue")
st.caption(
    "Use the filters below to focus on claims that warrant closer review based on current risk indicators."
)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Total Claims", f"{len(queue_df):,}")
metric_two.metric(
    "High-Risk Claims",
    f"{int((queue_df['risk_band'] == 'High Risk').sum()):,}",
)
metric_three.metric(
    "Critical-Risk Claims",
    f"{int((queue_df['risk_band'] == 'Critical Risk').sum()):,}",
)
metric_four.metric(
    "Total Flagged Claims",
    f"{int((queue_df['number_of_flags'] > 0).sum()):,}",
)

with st.container(border=True):
    st.subheader("Filters")
    filter_one, filter_two, filter_three = st.columns(3)
    filter_four, filter_five = st.columns((1, 1))

    available_risk_bands = ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]
    available_providers = sorted(queue_df["provider_name"].dropna().unique().tolist())
    available_provider_types = sorted(queue_df["provider_type"].dropna().unique().tolist())
    available_statuses = sorted(queue_df["claim_status"].dropna().unique().tolist())

    with filter_one:
        selected_risk_bands = st.multiselect(
            "Risk band",
            options=available_risk_bands,
            default=available_risk_bands,
        )
    with filter_two:
        selected_providers = st.multiselect(
            "Provider",
            options=available_providers,
            default=[],
            placeholder="All providers",
        )
    with filter_three:
        selected_provider_types = st.multiselect(
            "Provider type",
            options=available_provider_types,
            default=[],
            placeholder="All provider types",
        )
    with filter_four:
        selected_statuses = st.multiselect(
            "Claim status",
            options=available_statuses,
            default=[],
            placeholder="All statuses",
        )
    with filter_five:
        min_date = queue_df["claim_date"].min().date()
        max_date = queue_df["claim_date"].max().date()
        selected_date_range = st.date_input(
            "Claim date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

filtered_df = queue_df.copy()
filtered_df = filtered_df.loc[filtered_df["risk_band"].isin(selected_risk_bands)]

if selected_providers:
    filtered_df = filtered_df.loc[filtered_df["provider_name"].isin(selected_providers)]

if selected_provider_types:
    filtered_df = filtered_df.loc[filtered_df["provider_type"].isin(selected_provider_types)]

if selected_statuses:
    filtered_df = filtered_df.loc[filtered_df["claim_status"].isin(selected_statuses)]

if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
    start_date = pd.Timestamp(selected_date_range[0])
    end_date = pd.Timestamp(selected_date_range[1])
    filtered_df = filtered_df.loc[
        filtered_df["claim_date"].between(start_date, end_date, inclusive="both")
    ]

chart_count_df = (
    filtered_df.groupby("risk_band", as_index=False)
    .agg(claim_count=("claim_id", "count"))
)
chart_amount_df = (
    filtered_df.groupby("risk_band", as_index=False)
    .agg(total_claim_amount=("claim_amount", "sum"))
)
chart_count_df = sort_risk_band_frame(chart_count_df)
chart_amount_df = sort_risk_band_frame(chart_amount_df)

chart_left, chart_right = st.columns(2)
with chart_left:
    count_chart = styled_bar_chart(
        chart_count_df,
        x="risk_band",
        y="claim_count",
        color="risk_band",
        title="Count Of Claims By Risk Band",
    )
    count_chart.update_layout(showlegend=False)
    st.plotly_chart(count_chart, use_container_width=True)

with chart_right:
    amount_chart = styled_bar_chart(
        chart_amount_df,
        x="risk_band",
        y="total_claim_amount",
        color="risk_band",
        title="Total Claim Amount By Risk Band",
    )
    amount_chart.update_layout(showlegend=False)
    st.plotly_chart(amount_chart, use_container_width=True)

st.subheader("Scored Claims")
st.dataframe(
    filtered_df[
        [
            "claim_id",
            "member_id",
            "provider_name",
            "diagnosis_description",
            "claim_amount",
            "total_risk_score",
            "risk_band",
            "number_of_flags",
            "recommended_action",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "claim_amount": st.column_config.NumberColumn("Claim Amount", format="%.2f"),
        "total_risk_score": st.column_config.NumberColumn("Risk Score", format="%d"),
        "number_of_flags": st.column_config.NumberColumn("Review Flags", format="%d"),
    },
)

if not filtered_df.empty:
    selected_claim_id = st.selectbox(
        "Open a claim in the Risk Profile page",
        options=filtered_df["claim_id"].astype(str).tolist(),
        index=0,
    )
    if st.button("Set Selected Claim", use_container_width=False):
        st.session_state["selected_claim_id"] = selected_claim_id
        st.success(
            f"Claim {selected_claim_id} is now ready to inspect on the Claim Risk Profile page."
        )
