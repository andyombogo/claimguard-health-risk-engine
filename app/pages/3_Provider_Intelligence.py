"""Provider Intelligence page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard_utils import (
    apply_dashboard_theme,
    apply_status_overrides,
    build_provider_dashboard_summary,
    get_dashboard_data,
    initialize_dashboard_state,
    plotly_white_template,
)

import plotly.express as px

apply_dashboard_theme()
claims_df, flags_df, scored_df, queue_df = get_dashboard_data()
initialize_dashboard_state(claims_df)
queue_df = apply_status_overrides(queue_df)

provider_summary_df = build_provider_dashboard_summary(queue_df, flags_df)

st.title("Provider Intelligence")
st.caption(
    "Provider-level patterns help claims teams identify where additional context or follow-up may be useful."
)
st.info(
    "Provider-level patterns are screening indicators and should be interpreted with context."
)

st.subheader("Provider Summary")
st.dataframe(
    provider_summary_df[
        [
            "provider_id",
            "provider_name",
            "total_claims",
            "average_claim_amount",
            "high_risk_claims",
            "critical_risk_claims",
            "percentage_flagged",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "total_claims": st.column_config.NumberColumn("Total Claims", format="%d"),
        "average_claim_amount": st.column_config.NumberColumn(
            "Average Claim Amount", format="%.2f"
        ),
        "high_risk_claims": st.column_config.NumberColumn("High-Risk Claims", format="%d"),
        "critical_risk_claims": st.column_config.NumberColumn(
            "Critical-Risk Claims", format="%d"
        ),
        "percentage_flagged": st.column_config.NumberColumn(
            "Percentage Flagged", format="%.1f%%"
        ),
    },
)

top_volume_df = provider_summary_df.sort_values(
    "total_claims",
    ascending=False,
).head(10).sort_values("total_claims", ascending=True)
top_high_risk_df = provider_summary_df.sort_values(
    ["high_risk_claims", "critical_risk_claims", "total_claims"],
    ascending=False,
).head(10).sort_values("high_risk_claims", ascending=True)
top_average_amount_df = provider_summary_df.sort_values(
    "average_claim_amount",
    ascending=False,
).head(10).sort_values("average_claim_amount", ascending=True)

chart_one, chart_two = st.columns(2)
with chart_one:
    volume_chart = px.bar(
        top_volume_df,
        x="total_claims",
        y="provider_name",
        orientation="h",
        title="Top Providers By Claim Volume",
        template=plotly_white_template(),
        color="total_claims",
        color_continuous_scale="Blues",
    )
    volume_chart.update_layout(margin=dict(l=20, r=20, t=55, b=20), coloraxis_showscale=False)
    st.plotly_chart(volume_chart, use_container_width=True)

with chart_two:
    high_risk_chart = px.bar(
        top_high_risk_df,
        x="high_risk_claims",
        y="provider_name",
        orientation="h",
        title="Top Providers By High-Risk Claim Count",
        template=plotly_white_template(),
        color="high_risk_claims",
        color_continuous_scale="Oranges",
    )
    high_risk_chart.update_layout(
        margin=dict(l=20, r=20, t=55, b=20),
        coloraxis_showscale=False,
    )
    st.plotly_chart(high_risk_chart, use_container_width=True)

average_chart = px.bar(
    top_average_amount_df,
    x="average_claim_amount",
    y="provider_name",
    orientation="h",
    title="Average Claim Amount By Provider",
    template=plotly_white_template(),
    color="average_claim_amount",
    color_continuous_scale="Teal",
)
average_chart.update_layout(
    margin=dict(l=20, r=20, t=55, b=20),
    coloraxis_showscale=False,
)
st.plotly_chart(average_chart, use_container_width=True)
