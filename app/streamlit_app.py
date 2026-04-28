"""Landing page for the ClaimGuard Streamlit dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dashboard_utils import (
    apply_dashboard_theme,
    get_dashboard_data,
    initialize_dashboard_state,
    sort_risk_band_frame,
    styled_bar_chart,
)

st.set_page_config(
    page_title="ClaimGuard Health Risk Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_dashboard_theme()

claims_df, _flags_df, _scored_df, queue_df = get_dashboard_data()
initialize_dashboard_state(claims_df)

st.markdown(
    """
    <div class="claimguard-hero">
        <h1 style="margin:0 0 0.3rem 0;">ClaimGuard Health Risk Engine</h1>
        <p style="margin:0; font-size:1.02rem; max-width:58rem;">
            A transparent health claims triage prototype that helps claims officers prioritize
            review work using explainable risk indicators, provider patterns, and document checks.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
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
    "Claims With Review Flags",
    f"{int((queue_df['number_of_flags'] > 0).sum()):,}",
)

left_column, right_column = st.columns((1.1, 0.9))

with left_column:
    st.subheader("Problem Statement")
    st.write(
        "Claims officers often manage large volumes of submissions with limited time to "
        "spot duplicate patterns, unusual billing, diagnosis-treatment inconsistencies, "
        "missing documentation, and provider or member history signals early enough "
        "to prioritize review effectively."
    )

    st.subheader("How The Prototype Works")
    st.markdown(
        "- Loads synthetic health claims only.\n"
        "- Runs transparent review rules for duplicate patterns, billing, diagnosis-procedure fit, provider signals, and document checks.\n"
        "- Aggregates rule points into a claim-level risk score and risk band.\n"
        "- Presents the results in review-friendly queue, claim profile, provider intelligence, and audit views."
    )

    st.subheader("Navigation")
    st.markdown(
        "- Use **Claims Review Queue** to filter and prioritize current work.\n"
        "- Use **Claim Risk Profile** to inspect one claim in detail.\n"
        "- Use **Provider Intelligence** to review provider-level screening indicators.\n"
        "- Use **Audit Log** to view mock workflow actions and maker-checker context."
    )

with right_column:
    band_summary_df = (
        queue_df.groupby("risk_band", as_index=False)
        .agg(
            claim_count=("claim_id", "count"),
            total_claim_amount=("claim_amount", "sum"),
        )
    )
    band_summary_df = sort_risk_band_frame(band_summary_df)

    band_chart = styled_bar_chart(
        band_summary_df,
        x="risk_band",
        y="claim_count",
        color="risk_band",
        title="Current Claims By Risk Band",
    )
    band_chart.update_layout(showlegend=False)
    st.plotly_chart(band_chart, use_container_width=True)

    st.markdown(
        """
        <div class="claimguard-note">
            <strong>Responsible Use Note</strong><br/>
            ClaimGuard is a decision-support prototype. Review flags and risk scores are screening
            indicators that help prioritize verification work. They do not establish wrongdoing or
            replace human review.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Prototype Snapshot")
snapshot_df = queue_df[
    [
        "claim_id",
        "provider_name",
        "diagnosis_description",
        "claim_amount",
        "total_risk_score",
        "risk_band",
        "number_of_flags",
        "recommended_action",
    ]
].head(12)
st.dataframe(
    snapshot_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "claim_amount": st.column_config.NumberColumn("Claim Amount", format="%.2f"),
        "total_risk_score": st.column_config.NumberColumn("Risk Score", format="%d"),
        "number_of_flags": st.column_config.NumberColumn("Review Flags", format="%d"),
    },
)
