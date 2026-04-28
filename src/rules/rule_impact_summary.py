"""Rule-impact summaries for threshold calibration and demo QA."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.rules.run_all_rules import run_all_rules
from src.scoring.risk_score import score_claims
from src.utils.helpers import repo_root


def _dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """Render a small dataframe as a Markdown table without optional dependencies."""

    if frame.empty:
        return "_No rows._"

    columns = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in frame.iterrows():
        values = [str(row[column]) for column in frame.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_rule_impact_summary(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize how often each rule is triggered across a claims portfolio."""

    if "claim_id" not in claims_df.columns:
        raise ValueError("claims_df must contain a claim_id column.")

    flags_df = run_all_rules(claims_df)
    total_claims = max(len(claims_df), 1)
    if flags_df.empty:
        return pd.DataFrame(
            columns=[
                "rule_name",
                "flagged_claims",
                "percentage_of_claims",
                "total_points",
                "average_points",
                "top_severity",
            ]
        )

    severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    summary_df = (
        flags_df.groupby("rule_name", as_index=False)
        .agg(
            flagged_claims=("claim_id", "nunique"),
            total_points=("points", "sum"),
            average_points=("points", "mean"),
            top_severity=(
                "severity",
                lambda values: max(
                    values.astype(str).str.lower(),
                    key=lambda value: severity_rank.get(value, 0),
                ),
            ),
        )
        .sort_values(["flagged_claims", "total_points"], ascending=False)
        .reset_index(drop=True)
    )
    summary_df["percentage_of_claims"] = (
        summary_df["flagged_claims"] / total_claims * 100
    ).round(2)
    summary_df["average_points"] = summary_df["average_points"].round(2)
    return summary_df[
        [
            "rule_name",
            "flagged_claims",
            "percentage_of_claims",
            "total_points",
            "average_points",
            "top_severity",
        ]
    ]


def build_risk_band_summary(claims_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize the final risk-band distribution for a claims portfolio."""

    flags_df = run_all_rules(claims_df)
    scored_df = score_claims(claims_df, flags_df)
    return (
        scored_df.groupby("risk_band", as_index=False)
        .agg(
            claim_count=("claim_id", "count"),
            average_score=("total_risk_score", "mean"),
            max_score=("total_risk_score", "max"),
        )
        .sort_values("average_score", ascending=False)
        .assign(average_score=lambda frame: frame["average_score"].round(2))
        .reset_index(drop=True)
    )


def write_rule_impact_outputs(
    claims_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """Write CSV and Markdown summaries for the current synthetic portfolio."""

    root = repo_root()
    resolved_claims_path = Path(claims_path) if claims_path else root / "data" / "synthetic" / "synthetic_health_claims.csv"
    resolved_output_dir = Path(output_dir) if output_dir else root / "outputs"

    if not resolved_claims_path.exists():
        raise FileNotFoundError(
            f"Synthetic claims file not found at {resolved_claims_path}. "
            "Run `python src/data_processing/generate_synthetic_claims.py` first."
        )

    claims_df = pd.read_csv(resolved_claims_path)
    rule_summary_df = build_rule_impact_summary(claims_df)
    band_summary_df = build_risk_band_summary(claims_df)

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = resolved_output_dir / "rule_impact_summary.csv"
    markdown_path = resolved_output_dir / "rule_impact_summary.md"

    rule_summary_df.to_csv(csv_path, index=False)
    markdown_path.write_text(
        "# Rule Impact Summary\n\n"
        "This generated report helps calibrate ClaimGuard's transparent review rules using synthetic data only.\n\n"
        "## Rule Triggers\n\n"
        f"{_dataframe_to_markdown(rule_summary_df)}\n\n"
        "## Risk Band Distribution\n\n"
        f"{_dataframe_to_markdown(band_summary_df)}\n\n"
        "## Responsible Use Note\n\n"
        "Rule counts show screening signals for review prioritization. They do not confirm fraud or wrongdoing.\n",
        encoding="utf-8",
    )
    return csv_path, markdown_path


if __name__ == "__main__":
    csv_output_path, markdown_output_path = write_rule_impact_outputs()
    print(f"Wrote {csv_output_path}")
    print(f"Wrote {markdown_output_path}")
