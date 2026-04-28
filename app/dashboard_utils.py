"""Shared cached data and session helpers for the ClaimGuard Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.rules.run_all_rules import run_all_rules
from src.scoring.explainability import build_claim_risk_profile
from src.scoring.risk_band import risk_band_sort_value
from src.scoring.risk_score import score_claims
from src.workflow.triage_queue import build_triage_queue

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CLAIMS_PATH = REPO_ROOT / "data" / "synthetic" / "synthetic_health_claims.csv"

RISK_BAND_COLORS = {
    "Low Risk": "#6BA292",
    "Medium Risk": "#E6A23C",
    "High Risk": "#D9730D",
    "Critical Risk": "#B03A2E",
}

def apply_dashboard_theme() -> None:
    """Apply a lightweight professional theme to the dashboard."""

    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(23, 78, 116, 0.08), transparent 28%),
                linear-gradient(180deg, #f6f9fc 0%, #ffffff 42%, #f8fbfd 100%);
        }
        .claimguard-hero {
            padding: 1.35rem 1.5rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0f3d5e 0%, #1b5f82 60%, #4f8cae 100%);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 18px 40px rgba(15, 61, 94, 0.14);
            margin-bottom: 1rem;
        }
        .claimguard-chip {
            display: inline-block;
            padding: 0.32rem 0.65rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
            background: #eef5f9;
            color: #18445d;
            border: 1px solid #d8e6ee;
        }
        .claimguard-note {
            padding: 0.9rem 1rem;
            border-radius: 14px;
            border: 1px solid #d9e6f0;
            background: #f7fbff;
            color: #214b63;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stop_with_missing_data_message() -> None:
    """Show a helpful message when the synthetic dataset is unavailable."""

    st.error(
        "The dashboard could not find `data/synthetic/synthetic_health_claims.csv`."
    )
    st.markdown(
        "Generate the synthetic dataset first with:\n\n"
        "```powershell\n"
        "py -B src\\data_processing\\generate_synthetic_claims.py\n"
        "```"
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load claims data, run rules, calculate scores, and prepare the queue."""

    if not SYNTHETIC_CLAIMS_PATH.exists():
        raise FileNotFoundError(SYNTHETIC_CLAIMS_PATH)

    claims_df = pd.read_csv(
        SYNTHETIC_CLAIMS_PATH,
        parse_dates=["claim_date", "admission_date", "discharge_date"],
    )
    flags_df = run_all_rules(claims_df)
    scored_df = score_claims(claims_df, flags_df)
    queue_df = build_triage_queue(
        claims_df.rename(columns={"claim_amount": "claimed_amount"}),
        scored_df,
    )
    queue_df = queue_df.rename(columns={"claimed_amount": "claim_amount"})
    queue_df["claim_date"] = pd.to_datetime(queue_df["claim_date"], errors="coerce")
    return claims_df, flags_df, scored_df, queue_df


def get_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return cached dashboard data or stop with a clear message."""

    try:
        return load_dashboard_data()
    except FileNotFoundError:
        stop_with_missing_data_message()
        raise


def _seed_audit_log(claims_df: pd.DataFrame) -> list[dict[str, str]]:
    """Create a small mock audit history for the demo."""

    sample_claims = claims_df.head(3)["claim_id"].astype(str).tolist()
    seed_time = pd.Timestamp("2026-04-28 09:00:00")
    return [
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": sample_claims[0],
            "action": "Initial triage completed",
            "reviewer_role": "Claims Officer",
            "previous_status": "Submitted",
            "new_status": "Under Review",
            "note": "Claim reviewed against current rule set and queued for attention.",
        },
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": sample_claims[1],
            "action": "Sent to checker",
            "reviewer_role": "Claims Officer",
            "previous_status": "Under Review",
            "new_status": "Ready for Checker",
            "note": "Raised for second-level review because of multiple risk indicators.",
        },
        {
            "timestamp": (seed_time + pd.Timedelta(minutes=47)).strftime("%Y-%m-%d %H:%M"),
            "claim_id": sample_claims[2],
            "action": "Escalated for follow-up",
            "reviewer_role": "Senior Reviewer",
            "previous_status": "Ready for Checker",
            "new_status": "Escalated",
            "note": "Further verification recommended before approval.",
        },
    ]


def initialize_dashboard_state(claims_df: pd.DataFrame) -> None:
    """Initialize shared session state used across the dashboard pages."""

    if "selected_claim_id" not in st.session_state and not claims_df.empty:
        st.session_state["selected_claim_id"] = str(claims_df.iloc[0]["claim_id"])

    if "claim_notes" not in st.session_state:
        st.session_state["claim_notes"] = {}

    if "claim_status_overrides" not in st.session_state:
        st.session_state["claim_status_overrides"] = {}

    if "audit_log_records" not in st.session_state:
        st.session_state["audit_log_records"] = _seed_audit_log(claims_df)


def get_audit_log_df() -> pd.DataFrame:
    """Return the audit log as a dataframe sorted by most recent entries."""

    audit_log_df = pd.DataFrame(st.session_state.get("audit_log_records", []))
    if audit_log_df.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "claim_id",
                "action",
                "reviewer_role",
                "previous_status",
                "new_status",
                "note",
            ]
        )

    audit_log_df["timestamp"] = pd.to_datetime(audit_log_df["timestamp"], errors="coerce")
    audit_log_df = audit_log_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    audit_log_df["timestamp"] = audit_log_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    return audit_log_df


def append_audit_log_entry(
    claim_id: str,
    action: str,
    reviewer_role: str,
    previous_status: str,
    new_status: str,
    note: str,
) -> None:
    """Append a new session-level audit entry."""

    records = st.session_state.setdefault("audit_log_records", [])
    records.append(
        {
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "claim_id": str(claim_id),
            "action": action,
            "reviewer_role": reviewer_role,
            "previous_status": previous_status,
            "new_status": new_status,
            "note": note,
        }
    )


def apply_status_overrides(queue_df: pd.DataFrame) -> pd.DataFrame:
    """Overlay session-state workflow statuses onto the queue view."""

    overrides = st.session_state.get("claim_status_overrides", {})
    if not overrides:
        return queue_df

    updated_df = queue_df.copy()
    updated_df["claim_status"] = updated_df.apply(
        lambda row: overrides.get(str(row["claim_id"]), row["claim_status"]),
        axis=1,
    )
    return updated_df


def register_claim_action(
    queue_df: pd.DataFrame,
    claim_id: str,
    action: str,
    reviewer_role: str,
    new_status: str,
    note: str,
) -> None:
    """Update session state for a claim action and add an audit entry."""

    claim_id = str(claim_id)
    current_status = "Submitted"
    if not queue_df.empty:
        matches = queue_df.loc[queue_df["claim_id"].astype(str) == claim_id]
        if not matches.empty:
            current_status = str(matches.iloc[0]["claim_status"])

    previous_status = st.session_state.get("claim_status_overrides", {}).get(
        claim_id,
        current_status,
    )
    st.session_state.setdefault("claim_status_overrides", {})[claim_id] = new_status
    append_audit_log_entry(
        claim_id=claim_id,
        action=action,
        reviewer_role=reviewer_role,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
    )


def build_provider_dashboard_summary(queue_df: pd.DataFrame, flags_df: pd.DataFrame) -> pd.DataFrame:
    """Build provider-level metrics for the provider intelligence page."""

    flagged_claim_ids = set(flags_df["claim_id"].astype(str).tolist())
    provider_df = queue_df.copy()
    provider_df["is_flagged"] = provider_df["claim_id"].astype(str).isin(flagged_claim_ids)
    provider_df["is_high_risk"] = provider_df["risk_band"] == "High Risk"
    provider_df["is_critical_risk"] = provider_df["risk_band"] == "Critical Risk"

    summary_df = (
        provider_df.groupby(["provider_id", "provider_name"], dropna=False)
        .agg(
            total_claims=("claim_id", "count"),
            average_claim_amount=("claim_amount", "mean"),
            high_risk_claims=("is_high_risk", "sum"),
            critical_risk_claims=("is_critical_risk", "sum"),
            percentage_flagged=("is_flagged", "mean"),
        )
        .reset_index()
    )
    summary_df["percentage_flagged"] = summary_df["percentage_flagged"] * 100
    summary_df = summary_df.sort_values(
        ["high_risk_claims", "critical_risk_claims", "total_claims"],
        ascending=False,
    ).reset_index(drop=True)
    return summary_df


def build_claim_profile_data(
    claims_df: pd.DataFrame,
    flags_df: pd.DataFrame,
    queue_df: pd.DataFrame,
    claim_id: str,
) -> dict[str, object]:
    """Return a claim profile bundle for the detail page."""

    profile = build_claim_risk_profile(claims_df, flags_df, claim_id)
    queue_match = queue_df.loc[queue_df["claim_id"].astype(str) == str(claim_id)]
    if not queue_match.empty:
        profile["queue_row"] = queue_match.iloc[0].to_dict()
    return profile


def find_related_claims(queue_df: pd.DataFrame, claim_id: str) -> pd.DataFrame:
    """Find similar or related claims using same member or provider-diagnosis overlap."""

    claim_row_df = queue_df.loc[queue_df["claim_id"].astype(str) == str(claim_id)]
    if claim_row_df.empty:
        return pd.DataFrame()

    claim_row = claim_row_df.iloc[0]
    related_df = queue_df.loc[queue_df["claim_id"].astype(str) != str(claim_id)].copy()
    same_member_mask = related_df["member_id"] == claim_row["member_id"]
    same_provider_diagnosis_mask = (
        (related_df["provider_id"] == claim_row["provider_id"])
        & (related_df["diagnosis_code"] == claim_row["diagnosis_code"])
    )
    related_df = related_df.loc[same_member_mask | same_provider_diagnosis_mask].copy()
    if related_df.empty:
        return related_df

    related_df["relationship_hint"] = related_df.apply(
        lambda row: "Same member"
        if row["member_id"] == claim_row["member_id"]
        else "Same provider and diagnosis",
        axis=1,
    )
    related_df = related_df.sort_values(
        ["relationship_hint", "total_risk_score", "claim_date"],
        ascending=[True, False, False],
    )
    return related_df[
        [
            "claim_id",
            "claim_date",
            "provider_name",
            "diagnosis_description",
            "claim_amount",
            "total_risk_score",
            "risk_band",
            "relationship_hint",
        ]
    ].head(12)


def sort_risk_band_frame(frame: pd.DataFrame, band_column: str = "risk_band") -> pd.DataFrame:
    """Sort a dataframe by the standard risk-band order."""

    sorted_df = frame.copy()
    sorted_df["_risk_order"] = sorted_df[band_column].map(risk_band_sort_value)
    sorted_df = sorted_df.sort_values("_risk_order").drop(columns="_risk_order")
    return sorted_df


def plotly_white_template() -> str:
    """Return the standard Plotly template used across the dashboard."""

    return "plotly_white"


def styled_bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    orientation: str = "v",
) -> px.bar:
    """Create a consistently styled Plotly bar chart."""

    chart = px.bar(
        frame,
        x=x,
        y=y,
        color=color,
        color_discrete_map=RISK_BAND_COLORS if color == "risk_band" else None,
        title=title,
        template=plotly_white_template(),
        orientation=orientation,
    )
    chart.update_layout(
        legend_title_text="",
        margin=dict(l=20, r=20, t=55, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return chart
