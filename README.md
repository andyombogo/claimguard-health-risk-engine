# ClaimGuard Health Risk Engine

ClaimGuard is an explainable health claims triage prototype that helps medical claims officers prioritize which claims may need closer human review.

## Problem

Medical claims officers often review large volumes of claims under time pressure. Important signals can be buried in manual checks, scattered documents, and slow historical lookups. That makes it harder to spot duplicate patterns, abnormal billing, missing documents, or diagnosis-treatment mismatches early enough to prioritize review well.

## Solution

ClaimGuard combines synthetic claims data, transparent review rules, additive risk scoring, and a reviewer-friendly dashboard to help officers see higher-risk claims first and understand why they were prioritized.

## Features

- Synthetic health claims data generator with controlled risk patterns
- Modular rule engine for duplicate checks, abnormal billing, diagnosis-treatment mismatch, provider patterns, and document completeness
- Claim-level risk score, risk band, recommended action, and explanation layer
- Streamlit dashboard with review queue, claim profile, provider intelligence, and audit log views
- Optional FastAPI demo endpoint for single-claim scoring
- Unit tests for rule logic, scoring, and workflow behavior

## Quick Start

Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Generate the synthetic dataset:

```powershell
py -B src\data_processing\generate_synthetic_claims.py
```

Run the Streamlit app:

```powershell
streamlit run app/streamlit_app.py
```

Run the tests:

```powershell
pytest
```

Run the optional API:

```powershell
uvicorn api.main:app --reload
```

## Repository Structure

```text
claimguard-health-risk-engine/
|-- README.md
|-- ROADMAP.md
|-- data/
|-- docs/
|-- notebooks/
|-- src/
|-- app/
|-- api/
|-- tests/
`-- outputs/
```

## Responsible Use

ClaimGuard is a decision-support tool, not an automated accusation system.

- It highlights claims for review prioritization.
- It does not confirm fraud or wrongdoing.
- It should be used with human oversight.
- The repository uses synthetic data only.

## Roadmap

The current MVP focuses on explainable rules, claim-level scoring, dashboard-based triage, and a lightweight demo API. Planned next steps include fuzzy matching, richer provider and member intelligence, anomaly detection experiments, workflow hardening, and stronger audit support.

See [ROADMAP.md](./ROADMAP.md) for the phased plan.

## Documentation

- [Problem Statement](./docs/problem_statement.md)
- [User Persona](./docs/user_persona.md)
- [System Architecture](./docs/system_architecture.md)
- [Risk Scoring Logic](./docs/risk_scoring_logic.md)
- [Prototype Screens](./docs/prototype_screens.md)
- [Ethical Considerations](./docs/ethical_considerations.md)

## Author

Portfolio / demo owner: `Your Name Here`  
Project context: innovation challenge, hackathon, fellowship, or portfolio prototype
