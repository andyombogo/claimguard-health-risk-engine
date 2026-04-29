# Demo Summary

Live demo: <https://claimguard-health-risk-engine.streamlit.app/>

## Current Output
- Synthetic claims: 572
- Flagged claims: 280
- High-risk claims: 10
- Critical-risk claims: 2

## Top 5 Triggered Rule Types
- `missing_documents`: 168
- `provider_pattern_risk`: 64
- `near_duplicate_claim`: 58
- `diagnosis_treatment_mismatch`: 31
- `abnormal_billing`: 27

## Limitations
- The prototype uses synthetic data only and is not validated for live operational use.
- Rule quality depends on the accuracy and completeness of the input claim data.
- Duplicate and provider-pattern signals are stronger when richer historical context is available.
- A high score means a claim should be reviewed more closely, not that wrongdoing is confirmed.

## Next Steps
- Capture final screenshots from the live Streamlit app for the pitch deck.
- Add a reviewer feedback loop to mark whether each flag was useful, unclear, or not useful.
- Move demo audit persistence from CSV to SQLite for a stronger local pilot path.
- Expand synthetic scenarios across inpatient, outpatient, pharmacy, lab, and emergency claims.
- Add a calibration report that compares threshold changes before and after tuning.

## Recommended Pitch Flow
- Start with the landing page to frame the problem and show the live portfolio.
- Open the review queue and filter to high-risk or critical-risk claims.
- Open a claim profile and explain the score using the flagged rules.
- Move to provider intelligence to show portfolio-level screening context.
- Record a review action and show it in the audit log.

## Example Commands
- Generate synthetic data: `py -B src\data_processing\generate_synthetic_claims.py`
- Run Streamlit: `streamlit run app/streamlit_app.py`
- Run API: `uvicorn api.main:app --reload`
- Run tests: `pytest`
