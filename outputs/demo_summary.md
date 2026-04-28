# Demo Summary

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
- Persist reviewer actions so audit events survive dashboard refreshes.
- Show clearer related-claim context for same member, provider, diagnosis, and close claim dates.
- Move more rule thresholds into YAML and add a rule-impact calibration summary.
- Add API request/response examples plus endpoint tests for `/health` and `/score-claim`.
- Capture dashboard screenshots and add a short demo walkthrough for fellowship review.

## Example Commands
- Generate synthetic data: `py -B src\data_processing\generate_synthetic_claims.py`
- Run Streamlit: `streamlit run app/streamlit_app.py`
- Run API: `uvicorn api.main:app --reload`
- Run tests: `pytest`
