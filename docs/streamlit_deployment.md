# Streamlit Deployment Guide

This guide prepares ClaimGuard for a Streamlit Community Cloud demo deployment.

## Deployment Target

- Repository: `andyombogo/claimguard-health-risk-engine`
- Branch: `main`
- Streamlit entrypoint: `app/streamlit_app.py`
- Python version: `3.12`
- Streamlit dependency file: `app/requirements.txt`
- Full local/API dependency file: `requirements.txt`

## Fast Deploy Configuration

The deployed Streamlit app uses `app/requirements.txt`, not the root `requirements.txt`.

This is intentional. The root dependency file supports the full repository, including the optional FastAPI service, tests, and future experimentation. The dashboard deployment only needs Streamlit, Pandas, Plotly, Pydantic, PyYAML, and python-dotenv.

Keeping the Streamlit dependency file beside `app/streamlit_app.py` avoids installing unnecessary packages such as `pytest`, `fastapi`, `uvicorn`, `httpx`, and optional ML dependencies during Community Cloud deployment.

## Pre-Deployment Checklist

Run these commands from the repository root before deploying:

```powershell
python src/data_processing/generate_synthetic_claims.py
python -m src.rules.rule_impact_summary
pytest
streamlit run app/streamlit_app.py
```

Confirm:

- `data/synthetic/synthetic_health_claims.csv` exists.
- The dashboard opens locally.
- The Claims Review Queue shows scored claims.
- The Claim Risk Profile shows flags, explanations, and related-claim context.
- The Audit Log page can record and download review actions.
- Tests pass with `pytest`.

## Streamlit Community Cloud Steps

1. Open Streamlit Community Cloud.
2. Choose **Create app**.
3. Select the GitHub repository.
4. Set branch to `main`.
5. Set the main file path to `app/streamlit_app.py`.
6. In advanced settings, choose Python `3.12` if available.
7. Deploy the app.

If the app has already been building for a long time, stop that build or delete and redeploy the app after this dependency update is pushed. Python version changes require redeploying the app from Streamlit settings.

## Runtime Notes

ClaimGuard ships with synthetic demo data, so the deployed app should load without external data access.

The dashboard writes demo review actions to `outputs/review_audit_log.csv` when the deployment filesystem allows it. On hosted platforms this storage may be temporary, so the app also keeps session-state fallback behavior. For production, audit events should move to a real database.

## Responsible Use Reminder

The deployed app must be presented as a decision-support demo. Risk scores, review flags, and provider-level patterns are prioritization indicators only. They do not confirm fraud or wrongdoing.

## Troubleshooting

- If the app says synthetic data is missing, run `python src/data_processing/generate_synthetic_claims.py` locally and commit the generated CSV.
- If dependencies fail, confirm `app/requirements.txt` exists and the entrypoint is `app/streamlit_app.py`.
- If the build still tries to install API or test packages, check that Streamlit is using the `app/streamlit_app.py` entrypoint, not another file path.
- If imports fail, confirm the entrypoint is exactly `app/streamlit_app.py`.
- If audit actions do not persist after redeploy, this is expected for temporary hosted filesystems.
