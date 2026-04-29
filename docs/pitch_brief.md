# ClaimGuard Pitch Brief

## One-Line Pitch

ClaimGuard helps medical claims officers move from manual claim hunting to explainable, risk-based claim triage.

## Live Prototype

Live Streamlit demo: <https://claimguard-health-risk-engine.streamlit.app/>

Repository: <https://github.com/andyombogo/claimguard-health-risk-engine>

## The Problem

Medical claims officers often review high claim volumes under time pressure. The work is not only about reading one claim at a time. A reviewer also needs to check whether a claim looks similar to earlier submissions, whether billing is unusual for the diagnosis and procedure, whether treatment coding makes sense, whether key documents are missing, and whether provider or member history suggests the claim should be looked at more carefully.

Without a triage layer, those checks can be slow, scattered, and inconsistent.

## The Solution

ClaimGuard gives the reviewer a prioritized queue. Each claim receives a transparent risk score, a risk band, a recommended review action, and an explanation showing exactly which rules were triggered.

The system does not approve, reject, or accuse. It helps the claims officer decide what to review first and why.

## What The MVP Demonstrates

- Synthetic claims data with controlled review patterns
- Duplicate and near-duplicate claim checks
- Abnormal billing checks against diagnosis and procedure groups
- Diagnosis-treatment mismatch checks
- Missing document checks
- Provider and member pattern context
- Claim-level risk scoring and risk bands
- Reviewer-friendly dashboard with queue, claim profile, provider intelligence, and audit log
- Maker-checker and escalation workflow guidance
- Optional FastAPI scoring endpoint
- Unit tests and deployment-ready Streamlit app

## What To Show In A Three-Minute Demo

1. Open the live Streamlit app.
2. Start on the landing page and point out total claims, high-risk claims, and flagged claims.
3. Go to **Claims Review Queue** and filter to High Risk or Critical Risk.
4. Open **Claim Risk Profile** and show the flagged rules, points, explanations, and related claims.
5. Use a workflow button such as **Send To Checker** or **Escalate**.
6. Open **Audit Log** and show that the action is captured with timestamp, role, previous status, new status, and note.
7. Close with the responsible-use boundary: the final decision stays with the claims officer.

## Why This Is Useful In The Real World

ClaimGuard is designed around the reviewer's workflow. It does not ask a claims officer to trust a black-box result. It shows the signal, the rule, the score contribution, and the recommended next action.

For an insurer or health claims team, the value is faster prioritization, more consistent review, clearer escalation, and better auditability.

For a claimant or provider, the important safeguard is that the system does not label anyone as guilty or confirm wrongdoing. It only identifies claims that may need verification.

## Current Prototype Evidence

- Synthetic claims: 572
- Flagged claims: 280
- High-risk claims: 10
- Critical-risk claims: 2
- Test coverage: 33 passing pytest tests
- Live deployment: Streamlit Community Cloud

## Responsible Use Boundary

ClaimGuard is a decision-support prototype. A high score means "review this more carefully." It does not mean fraud is confirmed.

Before real-world use, the system would need data governance, privacy review, clinical and claims validation, fairness checks, secure authentication, database-backed audit logs, and human review policies.

## Best Next Step After The Fellowship Demo

The most valuable next step is a controlled pilot using de-identified or synthetic-like historical structures under a governance agreement. The pilot should measure whether ClaimGuard helps reviewers find review-worthy claims faster, document decisions more consistently, and reduce repeated manual checks without increasing unfair or unsupported flags.
