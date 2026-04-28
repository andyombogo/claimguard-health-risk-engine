# System Architecture

ClaimGuard is structured as a modular prototype so each part of the pipeline can be understood, tested, and extended independently. The current implementation is intentionally simple: synthetic data flows through a transparent rule engine, then into a scoring layer, dashboard, and optional API.

## Core Components

- **Synthetic claims data**
  - Stored under `data/synthetic/`
  - Used for demonstrations, tests, and UI walkthroughs
  - Includes controlled risky patterns to showcase duplicate, billing, document, and workflow signals

- **Data processing**
  - Cleans and normalizes claim fields
  - Validates schema expectations
  - Generates lightweight derived fields used by the rules

- **Rule engine**
  - Evaluates explainable checks such as:
    - exact and near duplicate claims
    - abnormal billing by diagnosis and procedure pattern
    - diagnosis-treatment mismatch
    - missing supporting documents
    - provider-level pattern risk

- **Risk scoring**
  - Aggregates rule points into a capped claim-level score
  - Assigns a risk band
  - Maps the band to a recommended review action
  - Preserves explanations for auditability

- **Dashboard**
  - Streamlit interface for reviewers
  - Presents queue, claim profile, provider intelligence, and audit log views

- **Optional API**
  - FastAPI endpoints for demo scoring and portfolio access
  - Supports simple prototype integration scenarios

- **Audit log**
  - Session-backed mock workflow history in the Streamlit prototype
  - Demonstrates maker-checker and escalation traceability

## Text-Based Architecture Diagram

```text
Synthetic Claims Data
data/synthetic/synthetic_health_claims.csv
        |
        v
Data Processing Layer
clean_claims.py -> validate_schema.py -> feature_engineering.py
        |
        v
Rule Engine
duplicate_claims.py
abnormal_billing.py
diagnosis_treatment_check.py
document_completeness.py
provider_pattern_check.py
        |
        v
Scoring And Explainability
risk_score.py -> risk_band.py -> explainability.py
        |
        +--------------------+
        |                    |
        v                    v
Streamlit Dashboard     FastAPI Demo API
app/                    api/
        |
        v
Audit-Friendly Review Outputs
queue, claim profile, provider view, session audit log
```

## Design Principles

- Explainability first
- Synthetic data only
- Human-in-the-loop review
- Modular components with clear interfaces
- Configurable rule logic through YAML
- Demo-ready outputs without overclaiming real-world readiness
